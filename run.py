#!/usr/bin/env python
"""Simple script to run the MineContext-v2 server."""

import argparse
import sys

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='MineContext-v2 Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run.py                    # Use default port from config (8000)
  python run.py -p 8080            # Run on port 8080
  python run.py --port 8050        # Run on port 8050
  python run.py -H 0.0.0.0 -p 8080 # Run on all interfaces, port 8080
  python run.py --debug            # Run in debug mode with auto-reload
        '''
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        help='Port to run the server on (default: from config.yaml, usually 8000)'
    )

    parser.add_argument(
        '-H', '--host',
        type=str,
        help='Host to bind the server to (default: from config.yaml, usually 127.0.0.1)'
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

        # Override settings with command line arguments
        host = args.host if args.host else settings.server.host
        port = args.port if args.port else settings.server.port
        debug = args.debug if args.debug else settings.server.debug

        print("=" * 60)
        print("MineContext-v2 Server")
        print("=" * 60)
        print(f"Server: http://{host}:{port}")
        print(f"API Docs: http://{host}:{port}/docs")
        print(f"Health: http://{host}:{port}/health")
        print("=" * 60)

        if args.port:
            print(f"📌 Using custom port: {port}")
        if args.host:
            print(f"📌 Using custom host: {host}")
        if debug:
            print(f"🔧 Debug mode: Enabled (auto-reload)")

        print("\nStarting server... Press Ctrl+C to stop\n")

        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=debug,
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)
