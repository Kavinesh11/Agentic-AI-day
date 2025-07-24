package com.example.ui

import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import io.flutter.plugin.common.MethodChannel
import io.flutter.embedding.engine.FlutterEngineCache

class FloatingWidgetService : Service() {
    private lateinit var windowManager: WindowManager
    private var floatingView: View? = null
    private var methodChannel: MethodChannel? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        addFloatingWidget()
        setupFlutterChannel()
    }

    private fun setupFlutterChannel() {
        val engine = FlutterEngineCache.getInstance().get("my_engine_id")
        if (engine != null) {
            methodChannel = MethodChannel(engine.dartExecutor.binaryMessenger, "floating_widget_channel")
        }
    }

    private fun addFloatingWidget() {
        val inflater = getSystemService(Context.LAYOUT_INFLATER_SERVICE) as LayoutInflater
        val resId = resources.getIdentifier("floating_widget", "layout", packageName)
        floatingView = inflater.inflate(resId, null)

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )

        params.gravity = Gravity.TOP or Gravity.START
        params.x = 0
        params.y = 100

        windowManager.addView(floatingView, params)

        // Drag and move
        floatingView?.setOnTouchListener(object : View.OnTouchListener {
            private var initialX = 0
            private var initialY = 0
            private var initialTouchX = 0f
            private var initialTouchY = 0f

            override fun onTouch(v: View?, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initialX = params.x
                        initialY = params.y
                        initialTouchX = event.rawX
                        initialTouchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        params.x = initialX + (event.rawX - initialTouchX).toInt()
                        params.y = initialY + (event.rawY - initialTouchY).toInt()
                        windowManager.updateViewLayout(floatingView, params)
                        return true
                    }
                }
                return false
            }
        })

        // Collapsed and expanded views
        val geminiBtn = floatingView?.findViewById<ImageButton>(resources.getIdentifier("btn_gemini", "id", packageName))
        val expandedLayout = floatingView?.findViewById<View>(resources.getIdentifier("expanded_buttons", "id", packageName))

        geminiBtn?.setOnClickListener {
            geminiBtn.visibility = View.GONE
            expandedLayout?.visibility = View.VISIBLE
        }

        // OCR Button
        val ocrBtn = floatingView?.findViewById<ImageButton>(resources.getIdentifier("btn_ocr", "id", packageName))
        ocrBtn?.setOnClickListener {
            val intent = Intent(this, ScreenshotActivity::class.java)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            startActivity(intent)
        }

        // Camera Button
        val camBtn = floatingView?.findViewById<ImageButton>(resources.getIdentifier("btn_camera", "id", packageName))
        camBtn?.setOnClickListener {
            // Bring app to foreground
            val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
            launchIntent?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            startActivity(launchIntent)

            // Give the app a moment to come to foreground, then send the event
            floatingView?.postDelayed({
                methodChannel?.invokeMethod("openCamera", null)
            }, 500) // 500ms delay
        }

        // Close Button
        val closeBtn = floatingView?.findViewById<ImageButton>(resources.getIdentifier("btn_close", "id", packageName))
        closeBtn?.setOnClickListener {
            stopSelf()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        floatingView?.let { windowManager.removeView(it) }
    }
} 