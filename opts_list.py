import subprocess
import re
import argparse
import sys

def get_android_devices(verbose=False):
    """Gets connected Android devices and their audio forwarding potential."""
    try:
        devices = []
        adb_output = subprocess.check_output(['adb', 'devices', '-l']).decode('utf-8')
        for line in adb_output.splitlines()[1:]:
            if line.strip() and not line.startswith('*'):
                match = re.match(r'([\w\d]+)\s+device(.*)', line)
                if match:
                    serial = match.group(1)
                    try:
                        sdk_version = int(subprocess.check_output(
                            ['adb', '-s', serial, 'shell', 'getprop', 'ro.build.version.sdk']
                        ).decode('utf-8').strip())
                        audio_possible = sdk_version >= 30
                        devices.append({
                            'serial': serial,
                            'audio_possible': audio_possible,
                            'full_info': line.strip(),
                            'sdk_version': sdk_version
                        })
                    except (subprocess.CalledProcessError, ValueError) as e:
                        if verbose:
                            print(f"Error getting SDK version for {serial}: {e}", file=sys.stderr) # Verbose error to stderr
        return devices
    except FileNotFoundError:
        print("Error: adb not found. Make sure it's in your PATH.", file=sys.stderr) # Error to stderr
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error communicating with adb: {e}", file=sys.stderr) # Error to stderr
        return []


def launch_scrcpy(serial, video_codec=None, max_size=None, max_fps=None, audio=True, keyboard_mode="default", verbose=False):
    """Launches scrcpy with specified options."""
    command = ['scrcpy', '-s', serial]

    if video_codec:
        command.extend(['--video-codec', video_codec])
    if max_size:
        command.extend(['-m', str(max_size)])
    if max_fps:
        command.extend(['--max-fps', str(max_fps)])
    if not audio:
        command.append('--no-audio')
    if keyboard_mode == "uhid":
        command.append("--keyboard=uhid")


    if verbose:
      print(f"Running command: {' '.join(command)}") # Verbose command echo

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: scrcpy not found. Make sure it's installed and in your PATH.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running scrcpy: {e}", file=sys.stderr)


if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(description="Launch scrcpy with options.")
    parser.add_argument("-s", "--serial", help="Serial number of the target device.")
    parser.add_argument("-v", "--video-codec", help="Video codec (e.g., h264, vp8).")
    parser.add_argument("-m", "--max-size", type=int, help="Maximum resolution.")
    parser.add_argument("-f", "--max-fps", type=int, help="Maximum frames per second.")
    parser.add_argument("-n", "--no-audio", action="store_true", help="Disable audio forwarding.")
    parser.add_argument("-k", "--keyboard-mode", choices=["default", "uhid"], default="default", help="Keyboard mode to use. Default or UHID")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("-l","--list-devices", action="store_true", help="List available devices and options.")

    args = parser.parse_args()

    if args.list_devices:
        devices = get_android_devices(args.verbose)
        if devices:
            for device in devices:
                print(f"Device: {device['full_info']}")
                print(f"  Serial: {device['serial']}")
                print(f"  SDK Version: {device['sdk_version']}")
                print(f"  Audio Forwarding Possible: {'Yes' if device['audio_possible'] else 'No'}")
                print("-" * 20)
        else:
            print("No devices found.")
        exit(0)

    if not args.serial:
        print("Error: Serial number (-s) is required unless --list-devices is used.")
        parser.print_help()
        exit(1)

    devices = get_android_devices(args.verbose)

    if devices:
      if args.verbose:
          for device in devices:
              print(f"Found device: {device['full_info']} (Audio: {'Possible' if device['audio_possible'] else 'Not Possible'})")
      launch_scrcpy(args.serial, args.video_codec, args.max_size, args.max_fps, not args.no_audio, args.keyboard_mode, args.verbose)
    else:
        exit(1)
