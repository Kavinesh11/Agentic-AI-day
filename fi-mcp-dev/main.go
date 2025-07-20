package main

import (
	"context"
	"fmt"
	"html/template"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"

	"github.com/epifi/fi-mcp-lite/middlewares"
	"github.com/epifi/fi-mcp-lite/pkg"
)

var authMiddleware *middlewares.AuthMiddleware

func main() {
	authMiddleware = middlewares.NewAuthMiddleware()
	s := server.NewMCPServer(
		"Hackathon MCP",
		"0.1.0",
		// Notifies clients when new tools gets added or any changes in tools
		server.WithInstructions("A financial portfolio management MCP server that provides secure access to users' financial data through Fi Money, a financial hub for all things money. This MCP server enables users to:\n- Access comprehensive net worth analysis with asset/liability breakdowns\n- Retrieve detailed transaction histories for mutual funds and Employee Provident Fund accounts\n- View credit reports with scores, loan details, and account histories, this also contains user's date of birth that can be used for calculating their age\n\nIf the person asks, you can tell about Fi Money that it is money management platform that offers below services in partnership with regulated entities:\n\nAVAILABLE SERVICES:\n- Digital savings account with zero Forex cards\n- Invest in Indian Mutual funds, US Stocks (partnership with licensed brokers), Smart and Fixed Deposits.\n- Instant Personal Loans \n- Faster UPI and Bank Transfers payments\n- Credit score monitoring and reports\n\nIMPORTANT LIMITATIONS:\n- This MCP server retrieves only actual user data via Net worth tracker and based on consent provided by the user  and does not generate hypothetical or estimated financial information\n- In this version of the MCP server, user's historical bank transactions, historical stocks transaction data, salary (unless categorically declared) is not present. Don't assume these data points for any kind of analysis.\n\nCRITICAL INSTRUCTIONS FOR FINANCIAL DATA:\n\n1. DATA BOUNDARIES: Only provide information that exists in the user's Fi Money Net worth tracker. Never estimate, extrapolate, or generate hypothetical financial data.\n\n2. SPENDING ANALYSIS: If user asks about spending patterns, categories, or analysis tell the user we currently don't offer that data through the MCP:\n   - For detailed spending insights, direct them to: \"For comprehensive spending analysis and categorization, please use the Fi Money mobile app which provides detailed spending insights and budgeting tools.\"\n\n3. MISSING DATA HANDLING: If requested data is not available:\n   - Clearly state what data is missing\n   - Explain how user can connect additional accounts in Fi Money app\n   - Never fill gaps with estimated or generic information\n"),
		server.WithToolCapabilities(true),
		server.WithResourceCapabilities(true, true),
		server.WithLogging(),
		server.WithToolHandlerMiddleware(authMiddleware.AuthMiddleware),
	)

	// Register tools from pkg.ToolList
	for _, tool := range pkg.ToolList {
		s.AddTool(mcp.NewTool(tool.Name, mcp.WithDescription(tool.Description)), dummyHandler)
	}

	// Configure streamable HTTP server with proper endpoints
	httpMux := http.NewServeMux()
	httpMux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	streamableServer := server.NewStreamableHTTPServer(s,
		server.WithEndpointPath("/stream"),
	)
	httpMux.Handle("/mcp/", streamableServer)
	httpMux.HandleFunc("/", rootHandler) // Add root handler
	httpMux.HandleFunc("/mockWebPage", webPageHandler)
	httpMux.HandleFunc("/login", loginHandler)
	
	// Add REST API endpoints
	httpMux.HandleFunc("/api/net-worth", apiNetWorthHandler)
	httpMux.HandleFunc("/api/credit-report", apiCreditReportHandler)
	httpMux.HandleFunc("/api/epf-details", apiEpfDetailsHandler)
	httpMux.HandleFunc("/api/mf-transactions", apiMfTransactionsHandler)
	httpMux.HandleFunc("/api/bank-transactions", apiBankTransactionsHandler)
	httpMux.HandleFunc("/api/stock-transactions", apiStockTransactionsHandler)
	
	port := pkg.GetPort()
	log.Println("starting server on port:", port)
	if servErr := http.ListenAndServe(fmt.Sprintf(":%s", port), httpMux); servErr != nil {
		log.Fatalln("error starting server", servErr)
	}
}

func dummyHandler(_ context.Context, _ mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return mcp.NewToolResultText("dummy handler"), nil
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	html := `
<!DOCTYPE html>
<html>
<head>
    <title>Fi MCP Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .method { color: #007cba; font-weight: bold; }
        .url { color: #d63638; font-family: monospace; }
        .description { color: #666; }
        .section { margin: 30px 0; }
        .api-section { background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .example { background: #f9f9f9; padding: 10px; border-left: 4px solid #007cba; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Fi MCP Server</h1>
    <p>Welcome to the Fi Money MCP (Model Context Protocol) Server. This server provides financial portfolio management capabilities.</p>
    
    <div class="api-section">
        <h2>🚀 REST API Endpoints (For Application Integration)</h2>
        <p>Use these endpoints to integrate financial data directly into your applications:</p>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/net-worth?phoneNumber=1111111111</span></div>
            <div class="description">Get comprehensive net worth data including assets and liabilities</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/credit-report?phoneNumber=1111111111</span></div>
            <div class="description">Get credit report with scores, loans, and payment history</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/epf-details?phoneNumber=1111111111</span></div>
            <div class="description">Get EPF account information and contribution history</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/mf-transactions?phoneNumber=1111111111</span></div>
            <div class="description">Get mutual fund transaction history</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/bank-transactions?phoneNumber=1111111111</span></div>
            <div class="description">Get bank transaction history</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/api/stock-transactions?phoneNumber=1111111111</span></div>
            <div class="description">Get Indian stock transaction history</div>
        </div>
        
        <h3>📋 Available Test Phone Numbers:</h3>
        <div class="example">
            <strong>Basic Scenarios:</strong><br>
            1111111111 (No assets), 2222222222 (All assets), 3333333333 (Small portfolio)<br>
            4444444444 (Multiple banks), 5555555555 (No credit score), 6666666666 (No bank account)
        </div>
        <div class="example">
            <strong>Investment Profiles:</strong><br>
            7777777777 (Debt-heavy), 8888888888 (SIP Samurai), 9999999999 (Fixed Income)<br>
            1010101010 (Gold investor), 1313131313 (Balanced Growth), 1616161616 (Early Retirement)
        </div>
        
        <h3>🔧 Usage Examples:</h3>
        <div class="example">
            <strong>cURL Example:</strong><br>
            <code>curl "http://localhost:8080/api/net-worth?phoneNumber=2222222222"</code>
        </div>
        <div class="example">
            <strong>JavaScript Example:</strong><br>
            <code>fetch('http://localhost:8080/api/credit-report?phoneNumber=2222222222')<br>
            .then(response => response.json())<br>
            .then(data => console.log(data));</code>
        </div>
    </div>
    
    <div class="section">
        <h2>🔗 MCP Endpoints (For AI Assistants)</h2>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/mockWebPage?sessionId=YOUR_SESSION_ID</span></div>
            <div class="description">Web page for authentication with session ID parameter</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">POST</span> <span class="url">/login</span></div>
            <div class="description">Login endpoint (requires sessionId and phoneNumber form data)</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">WebSocket</span> <span class="url">/mcp/stream</span></div>
            <div class="description">MCP streamable server endpoint for tool interactions</div>
        </div>
        
        <div class="endpoint">
            <div><span class="method">GET</span> <span class="url">/static/</span></div>
            <div class="description">Static files (CSS, JS, images)</div>
        </div>
        
        <h3>Quick Start for MCP:</h3>
        <p>To access the web interface, visit: <a href="/mockWebPage?sessionId=test123">/mockWebPage?sessionId=test123</a></p>
    </div>
</body>
</html>`
	w.Write([]byte(html))
}

func webPageHandler(w http.ResponseWriter, r *http.Request) {
	sessionId := r.URL.Query().Get("sessionId")
	if sessionId == "" {
		http.Error(w, "sessionId is required", http.StatusBadRequest)
		return
	}

	tmpl, err := template.ParseFiles("static/login.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	data := struct {
		SessionId            string
		AllowedMobileNumbers []string
	}{
		SessionId:            sessionId,
		AllowedMobileNumbers: pkg.GetAllowedMobileNumbers(),
	}

	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	sessionId := r.FormValue("sessionId")
	phoneNumber := r.FormValue("phoneNumber")

	if sessionId == "" || phoneNumber == "" {
		http.Error(w, "sessionId and phoneNumber are required", http.StatusBadRequest)
		return
	}

	authMiddleware.AddSession(sessionId, phoneNumber)

	tmpl, err := template.ParseFiles("static/login_successful.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	err = tmpl.Execute(w, nil)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

// API Handlers for REST endpoints
func apiNetWorthHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_net_worth.json")
}

func apiCreditReportHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_credit_report.json")
}

func apiEpfDetailsHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_epf_details.json")
}

func apiMfTransactionsHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_mf_transactions.json")
}

func apiBankTransactionsHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_bank_transactions.json")
}

func apiStockTransactionsHandler(w http.ResponseWriter, r *http.Request) {
	handleAPIRequest(w, r, "fetch_stock_transactions.json")
}

// Generic handler for API requests
func handleAPIRequest(w http.ResponseWriter, r *http.Request, filename string) {
	// Set CORS headers for cross-origin requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
	w.Header().Set("Content-Type", "application/json")

	// Handle preflight requests
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Get phone number from query parameter or header
	phoneNumber := r.URL.Query().Get("phoneNumber")
	if phoneNumber == "" {
		phoneNumber = r.Header.Get("X-Phone-Number")
	}

	// If no phone number provided, return error
	if phoneNumber == "" {
		http.Error(w, `{"error": "phoneNumber is required. Add ?phoneNumber=1111111111 to URL or X-Phone-Number header"}`, http.StatusBadRequest)
		return
	}

	// Check if phone number is allowed
	allowedNumbers := pkg.GetAllowedMobileNumbers()
	isAllowed := false
	for _, allowed := range allowedNumbers {
		if allowed == phoneNumber {
			isAllowed = true
			break
		}
	}

	if !isAllowed {
		http.Error(w, `{"error": "Invalid phone number. Use one of the allowed test numbers"}`, http.StatusBadRequest)
		return
	}

	// Construct file path
	filePath := filepath.Join("test_data_dir", phoneNumber, filename)

	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.Error(w, `{"error": "Data not available for this phone number"}`, http.StatusNotFound)
		return
	}

	// Read and return the JSON file
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		http.Error(w, `{"error": "Failed to read data file"}`, http.StatusInternalServerError)
		return
	}

	w.Write(data)
}
