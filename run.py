#!/usr/bin/env python3
"""
Quick Commerce Price Comparison App Launcher
Run this script to start the Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Main function to launch the Streamlit app."""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the script directory
    os.chdir(script_dir)
    
    print("🚀 Starting Quick Commerce Price Comparison App...")
    print("📁 Working directory:", script_dir)
    print("🌐 The app will open in your browser at http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    print("-" * 60)
    
    try:
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running the application: {e}")
        print("💡 Make sure you have installed all requirements:")
        print("   pip install -r requirements.txt")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it:")
        print("   pip install streamlit")

if __name__ == "__main__":
    main()
