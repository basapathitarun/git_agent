#!/bin/bash

# ==============================================================================
# 🚀 SMOKE TEST RUNNER (TYPE FIX)
# ==============================================================================

# 🎨 Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 🔧 Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
TEMP_TEST_FILE="$PROJECT_ROOT/temp_smoke_runner.py"
REPORT_DIR="$PROJECT_ROOT/reports"
SMOKE_PR_NUMBER="9999"

# ------------------------------------------------------------------------------
# 1️⃣ Pre-flight Checks
# ------------------------------------------------------------------------------
echo -e "${BLUE}[INFO] Starting Smoke Test...${NC}"

if [ -d "$VENV_PATH" ]; then
    echo -e "${BLUE}[INFO] Activating virtual environment...${NC}"
    if [ -f "$VENV_PATH/Scripts/activate" ]; then
        source "$VENV_PATH/Scripts/activate"
    else
        source "$VENV_PATH/bin/activate"
    fi
else
    echo -e "${RED}[ERROR] Virtual environment not found at $VENV_PATH${NC}"
    exit 1
fi

export PYTHONPATH=$PROJECT_ROOT

# ------------------------------------------------------------------------------
# 2️⃣ Clean Up Old Artifacts
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 1] Cleaning up old artifacts...${NC}"
rm -f "$REPORT_DIR/PR_${SMOKE_PR_NUMBER}_Report.md"
echo "  ✓ Removed old reports"

# ------------------------------------------------------------------------------
# 3️⃣ Create Temporary Python Test Runner
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 2] Generating test runner...${NC}"

cat << 'EOF' > "$TEMP_TEST_FILE"
import os
import sys
from database import get_session, init_db, PRMetadata, PRReport
from burr_workflow import build_burr_app
from config import settings

# --- CONFIG ---
SMOKE_ID = 9999   # Integer for PRMetadata
PR_NUMBER = 9999

def seed_db():
    print("  🌱 Seeding Database with Mock PR...")
    init_db()
    db = get_session()
    
    # ✅ FIX 1: Use str(SMOKE_ID) for PRReport because pr_id is a String column
    db.query(PRReport).filter(PRReport.pr_id == str(SMOKE_ID)).delete()
    
    # ✅ FIX 2: Use SMOKE_ID (int) for PRMetadata because id is an Integer column
    db.query(PRMetadata).filter(PRMetadata.pr_number == PR_NUMBER).delete()
    
    # Insert Mock PR
    dummy_pr = PRMetadata(
        id=SMOKE_ID,  # Integer
        pr_number=PR_NUMBER,
        title="Smoke Test: Type Safety Check",
        author="script_bot",
        url="https://github.com/test/repo/pull/9999",
        repo="smoke-repo",
        files=[{
            "filename": "smoke_service.py",
            "status": "modified",
            "additions": 10,
            "deletions": 2,
            "patch": "@@ -1,5 +1,8 @@\n def check_status():\n-    return 'PENDING'\n+    return 'ACTIVE'"
        }]
    )
    db.add(dummy_pr)
    db.commit()
    db.close()
    print("  ✓ Database seeded.")

def run_pipeline():
    print("  🚀 Running Burr Workflow...")
    app = build_burr_app()
    app.run(halt_after=["persist_report"])
    print("  ✓ Workflow finished.")

def verify():
    print("  🔍 Verifying Results...")
    db = get_session()
    
    # ✅ FIX 3: Query using String for PRReport
    record = db.query(PRReport).filter(PRReport.pr_id == str(SMOKE_ID)).first()
    
    if not record:
        print("  ❌ FAIL: Database record missing.")
        sys.exit(1)
    
    print(f"  ✅ PASS: Database record found (ID: {record.id})")
    
    # Check File
    expected_path = os.path.join(settings.REPORTS_DIR, f"PR_{PR_NUMBER}_Report.md")
    
    if os.path.exists(expected_path):
        print(f"  ✅ PASS: Report file found at {expected_path}")
    else:
        print(f"  ❌ FAIL: Report file missing at {expected_path}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        seed_db()
        run_pipeline()
        verify()
    except Exception as e:
        print(f"  ❌ EXCEPTION: {e}")
        # import traceback
        # traceback.print_exc()
        sys.exit(1)
EOF

# ------------------------------------------------------------------------------
# 4️⃣ Execution
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 3] Running Python Logic...${NC}"
python "$TEMP_TEST_FILE"
EXIT_CODE=$?

# ------------------------------------------------------------------------------
# 5️⃣ Cleanup & Exit
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[STEP 4] Cleaning up temp files...${NC}"
rm -f "$TEMP_TEST_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✨ SMOKE TEST PASSED SUCCESSFULLY! ✨${NC}"
    exit 0
else
    echo -e "${RED}💀 SMOKE TEST FAILED with exit code $EXIT_CODE${NC}"
    exit 1
fi