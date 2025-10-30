#!/usr/bin/env python
"""Enhanced run script with automatic port detection."""

import argparse
import socket
import sys


def find_free_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port.

    Args:
        start_port: Port to start searching from
        max_attempts: Maximum number of ports to try

    Returns:
        Available port number

    Raises:
        RuntimeError: If no free port found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                s.close()
                return port
        except OSError:
            # Port is in use, try next one
            continue

    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='MineContext-v2 Server with Auto Port Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_auto_port.py                    # Auto-detect available port starting from 8000
  python run_auto_port.py -p 8080            # Try port 8080, auto-find if occupied
  python run_auto_port.py --start-port 9000  # Start searching from port 9000
  python run_auto_port.py --no-auto          # Don't auto-detect, fail if port occupied
  python run_auto_port.py --debug            # Run in debug mode with auto-reload
        '''
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        help='Preferred port to run on (will auto-find if occupied, unless --no-auto)'
    )

    parser.add_argument(
        '--start-port',
        type=int,
        default=8000,
        help='Starting port for auto-detection (default: 8000)'
    )

    parser.add_argument(
        '-H', '--host',
        type=str,
        help='Host to bind to (default: from config.yaml, usually 127.0.0.1)'
    )

    parser.add_argument(
        '--no-auto',
        action='store_true',
        help='Disable auto port detection, fail if port is occupied'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode with auto-reload'
    )

    return parser.parse_args()


if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_args()

        from backend.main import app, settings
        import uvicorn

        # Determine host
        host = args.host if args.host else settings.server.host

        # Determine port
        if args.no_auto:
            # No auto-detection, use specified or default port
            port = args.port if args.port else settings.server.port
        else:
            # Auto-detect available port
            start_port = args.port if args.port else args.start_port
            try:
                port = find_free_port(start_port)
                if port != start_port:
                    print(f"⚠️  Port {start_port} is occupied")
                    print(f"✅ Found available port: {port}")
            except RuntimeError as e:
                print(f"❌ Error: {e}")
                sys.exit(1)

        debug = args.debug if args.debug else settings.server.debug

        print("=" * 60)
        print("🚀 MineContext-v2 Server (Auto Port Detection)")
        print("=" * 60)
        print(f"Server:       http://{host}:{port}")
        print(f"API Docs:     http://{host}:{port}/docs")
        print(f"TodoList:     http://{host}:{port}/todolist/frontend/my-todos.html")
        print(f"Health Check: http://{host}:{port}/health")
        print("=" * 60)

        if args.port and port != args.port:
            print(f"📌 Requested port {args.port} was occupied, using {port} instead")
        if args.host:
            print(f"📌 Using custom host: {host}")
        if debug:
            print(f"🔧 Debug mode: Enabled (auto-reload)")

        print("\n💡 Tip: Save this port to your config to use it next time!")
        print(f"   Edit config.yaml and set: server.port = {port}")
        print("\nStarting server... Press Ctrl+C to stop\n")

        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=debug,
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped gracefully")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
