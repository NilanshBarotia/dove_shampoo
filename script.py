import os
import sys
import subprocess
from datetime import datetime

# ===================== 🔥 MSVC AUTO-BOOTSTRAP (ANY TERMINAL) =====================
def ensure_msvc():
    try:
        subprocess.check_output(["where", "cl"], stderr=subprocess.DEVNULL)
        return
    except Exception:
        pass

    vswhere = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    if not os.path.exists(vswhere):
        print("ERROR: vswhere.exe not found (Visual Studio Installer missing)")
        sys.exit(1)

    try:
        vs_path = subprocess.check_output(
            [
                vswhere,
                "-latest",
                "-products", "*",
                "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property", "installationPath",
            ],
            text=True
        ).strip()
    except Exception:
        print("ERROR: Failed to query Visual Studio installation")
        sys.exit(1)

    if not vs_path:
        print("ERROR: Visual Studio with C++ Build Tools not found")
        sys.exit(1)

    vsdevcmd = os.path.join(vs_path, "Common7", "Tools", "VsDevCmd.bat")
    if not os.path.exists(vsdevcmd):
        print("ERROR: VsDevCmd.bat not found in Visual Studio installation")
        sys.exit(1)

    cmd = f'"{vsdevcmd}" && python "{sys.argv[0]}"'
    subprocess.call(cmd, shell=True)
    sys.exit(0)

ensure_msvc()
# ===============================================================================


# 🔥 FINAL WINDOWS FIX (ENCODING + RICH + TQDM + GPU + NVCC)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["RICH_DISABLE"] = "1"
os.environ["TQDM_DISABLE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# 🔥 CRITICAL NVCC FIX
os.environ["VSCMD_ARG_TGT_ARCH"] = "x64"
os.environ["CUDAHOSTCXX"] = "cl.exe"
# 🔥 FORCE NVCC TO TRUST CURRENT MSVC ENV (CRITICAL)
os.environ["NVCC_PREPEND_FLAGS"] = "--compiler-bindir=cl.exe"
os.environ["CUDACXX"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin\nvcc.exe"



# ================= CONFIG =================
VIDEO_PATH = "test.mp4"
RUNS_DIR = "runs"
NERF_MODEL = "splatfacto"
# ==========================================


def run_command(command: str, step: str):
    print(f"\n [{step}]")
    print(command)

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy()
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"{step} FAILED")


def check_video():
    if not os.path.isfile(VIDEO_PATH):
        print(f" Video not found: {VIDEO_PATH}")
        sys.exit(1)
    print(" Video found")


def create_run_dirs():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RUNS_DIR, f"run_{ts}")

    paths = {
        "run": run_dir,
        "frames": os.path.join(run_dir, "frames", "images"),
        "colmap": os.path.join(run_dir, "colmap"),
        "dataset": os.path.join(run_dir, "dataset"),
        "outputs": os.path.join(run_dir, "outputs"),
        "exports": os.path.join(run_dir, "exports"),
    }

    for p in paths.values():
        os.makedirs(p, exist_ok=True)

    return paths


def extract_frames(paths):
    run_command(
        f'ffmpeg -i "{VIDEO_PATH}" -qscale:v 2 "{paths["frames"]}/frame_%04d.jpg"',
        "FFMPEG FRAME EXTRACTION"
    )


def run_colmap(paths):
    db = os.path.join(paths["colmap"], "database.db")
    sparse = os.path.join(paths["colmap"], "sparse")

    os.makedirs(sparse, exist_ok=True)

    run_command(
        f'colmap feature_extractor '
        f'--database_path "{db}" '
        f'--image_path "{paths["frames"]}" '
        f'--ImageReader.single_camera 1',
        "COLMAP FEATURE EXTRACTION"
    )

    run_command(
        f'colmap exhaustive_matcher --database_path "{db}"',
        "COLMAP MATCHING"
    )

    run_command(
        f'colmap mapper '
        f'--database_path "{db}" '
        f'--image_path "{paths["frames"]}" '
        f'--output_path "{sparse}"',
        "COLMAP MAPPING"
    )


def create_transforms(paths):
    src = os.path.join(paths["colmap"], "sparse", "0")
    dst = os.path.join(paths["dataset"], "colmap", "sparse", "0")
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    run_command(
        f'xcopy "{src}" "{dst}" /E /I /Y',
        "COPY COLMAP MODEL INTO DATASET"
    )

    run_command(
        f'python -m nerfstudio.scripts.process_data images '
        f'--data "{paths["frames"]}" '
        f'--output-dir "{paths["dataset"]}" '
        f'--skip-colmap '
        f'--colmap-model-path colmap\\sparse\\0',
        "COLMAP → TRANSFORMS.JSON"
    )


def train_nerf(paths):
    run_command(
        f'python -m nerfstudio.scripts.train {NERF_MODEL} '
        f'--data "{paths["dataset"]}" '
        f'--output-dir "{paths["outputs"]}"',
        "NERF / GAUSSIAN TRAINING"
    )


def export_splat(paths):
    splat_root = os.path.join(paths["outputs"], "splatfacto")

    runs = os.listdir(splat_root)
    if not runs:
        raise RuntimeError("No splatfacto run found for export")

    latest_run = sorted(runs)[-1]
    config_path = os.path.join(
        splat_root, latest_run, "config.yml"
    )

    run_command(
        f'python -m nerfstudio.scripts.export gaussian-splat '
        f'--load-config "{config_path}" '
        f'--output-dir "{paths["exports"]}"',
        "EXPORT .SPLAT"
    )


def main():
    try:
        check_video()
        paths = create_run_dirs()
        extract_frames(paths)
        run_colmap(paths)
        create_transforms(paths)
        train_nerf(paths)
        export_splat(paths)

        print("\n PIPELINE COMPLETED SUCCESSFULLY")
        print(f" .splat file is in: {paths['exports']}")

    except Exception as e:
        print("\nPIPELINE FAILED")
        print("ERROR:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
