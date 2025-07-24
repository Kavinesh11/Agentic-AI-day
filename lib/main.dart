import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:io';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Raseed',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const platform = MethodChannel('floating_widget_channel');

  Future<void> _requestOverlayPermission() async {
    if (!await Permission.systemAlertWindow.isGranted) {
      await Permission.systemAlertWindow.request();
    }
    // Open Android overlay settings if still not granted
    if (!await Permission.systemAlertWindow.isGranted) {
      await platform.invokeMethod('requestOverlayPermission');
    }
  }

  Future<void> _startFloatingWidget() async {
    await _requestOverlayPermission();
    await platform.invokeMethod('startFloatingWidget');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gemini Floater')),
      body: Center(
        child: ElevatedButton(
          onPressed: _startFloatingWidget,
          child: const Text('Start Floating Widget'),
        ),
      ),
    );
  }
}

class FloatingButtonOverlay extends StatefulWidget {
  final VoidCallback onOcrTap;
  final VoidCallback onCameraTap;
  const FloatingButtonOverlay({
    required this.onOcrTap,
    required this.onCameraTap,
    Key? key,
  }) : super(key: key);

  @override
  State<FloatingButtonOverlay> createState() => _FloatingButtonOverlayState();
}

class _FloatingButtonOverlayState extends State<FloatingButtonOverlay> with SingleTickerProviderStateMixin {
  late Offset position;
  bool expanded = false;
  late AnimationController _controller;
  late Animation<double> _expandAnim;

  @override
  void initState() {
    super.initState();
    // Set default position to bottom right after layout
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final size = MediaQuery.of(context).size;
      setState(() {
        position = Offset(20, 20); // 20 px from right and bottom
      });
    });
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 250),
    );
    _expandAnim = CurvedAnimation(parent: _controller, curve: Curves.easeInOut);
  }

  void _toggleExpand() {
    setState(() {
      expanded = !expanded;
      if (expanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final buttonSize = 64.0;
    return Positioned(
      right: position.dx,
      bottom: position.dy,
      child: GestureDetector(
        onPanUpdate: (details) {
          setState(() {
            double newRight = (position.dx - details.delta.dx).clamp(0, screenSize.width - buttonSize);
            double newBottom = (position.dy - details.delta.dy).clamp(0, screenSize.height - buttonSize - 24);
            position = Offset(newRight, newBottom);
          });
        },
        child: _buildButton(context),
      ),
    );
  }

  Widget _buildButton(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        SizeTransition(
          sizeFactor: _expandAnim,
          axis: Axis.vertical,
          axisAlignment: -1.0,
          child: expanded ? _buildActions(context) : SizedBox.shrink(),
        ),
        Material(
          elevation: 10,
          shape: CircleBorder(),
          color: Theme.of(context).colorScheme.primary,
          child: InkWell(
            onTap: _toggleExpand,
            customBorder: CircleBorder(),
            child: AnimatedContainer(
              duration: Duration(milliseconds: 200),
              width: 64,
              height: 64,
              child: Icon(
                expanded ? Icons.close : Icons.add,
                color: Colors.white,
                size: 36,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActions(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Container(
        margin: EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 8)],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _ActionButton(
              icon: Icons.text_fields,
              label: 'OCR',
              onTap: () {
                _toggleExpand();
                widget.onOcrTap();
              },
            ),
            Divider(height: 1),
            _ActionButton(
              icon: Icons.camera_alt,
              label: 'Camera',
              onTap: () {
                _toggleExpand();
                widget.onCameraTap();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _ActionButton({required this.icon, required this.label, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.black87),
            SizedBox(width: 12),
            Text(label, style: TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }
}

class OcrReaderScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('OCR Reader')),
      body: Center(child: Text('OCR Reader Placeholder')), // Placeholder
    );
  }
}

class CameraPreviewScreen extends StatelessWidget {
  final String imagePath;
  const CameraPreviewScreen({required this.imagePath});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Camera Preview')),
      body: Center(
        child: Image.file(File(imagePath)),
      ),
    );
  }
} 