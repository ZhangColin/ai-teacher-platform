#!/bin/bash
# 端点扫描和对比工具
#
# 快速扫描并对比 Python 和 Java 后端的 API 端点

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   API 端点扫描和对比工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 临时文件
PYTHON_JSON="/tmp/python-endpoints-$(date +%s).json"
JAVA_JSON="/tmp/java-endpoints-$(date +%s).json"
REPORT_MD="/tmp/endpoint-diff-$(date +%s).md"
RESULT_JSON="/tmp/compare-result-$(date +%s).json"

# 步骤 1: 扫描 Python 端点
echo -e "${YELLOW}步骤 1/4: 扫描 Python FastAPI 端点...${NC}"
python3 scripts/scan-python-endpoints.py > "$PYTHON_JSON"
PYTHON_COUNT=$(jq 'length' "$PYTHON_JSON")
echo -e "${GREEN}✓ 找到 $PYTHON_COUNT 个 Python 端点${NC}"
echo ""

# 步骤 2: 扫描 Java 端点
echo -e "${YELLOW}步骤 2/4: 扫描 Java Spring Boot 端点...${NC}"
python3 scripts/scan-java-endpoints.py > "$JAVA_JSON"
JAVA_COUNT=$(jq 'length' "$JAVA_JSON")
echo -e "${GREEN}✓ 找到 $JAVA_COUNT 个 Java 端点${NC}"
echo ""

# 步骤 3: 生成对比报告
echo -e "${YELLOW}步骤 3/4: 生成对比报告...${NC}"
python3 scripts/compare-endpoints.py "$PYTHON_JSON" "$JAVA_JSON" "$REPORT_MD" > "$RESULT_JSON"
echo -e "${GREEN}✓ 报告已生成${NC}"
echo ""

# 步骤 4: 显示摘要
echo -e "${YELLOW}步骤 4/4: 显示摘要${NC}"
echo -e "${GREEN}========================================${NC}"
COVERAGE=$(jq -r '.coverage' "$RESULT_JSON")
COMMON=$(jq '.common | length' "$RESULT_JSON")
ONLY_PYTHON=$(jq '.only_in_python | length' "$RESULT_JSON")
ONLY_JAVA=$(jq '.only_in_java | length' "$RESULT_JSON")

echo -e "Python 端点总数: ${GREEN}$PYTHON_COUNT${NC}"
echo -e "Java 端点总数:  ${GREEN}$JAVA_COUNT${NC}"
echo -e "迁移覆盖率:     ${YELLOW}$COVERAGE${NC}"
echo ""
echo -e "共同端点:       ${GREEN}$COMMON${NC}"
echo -e "仅在 Python:    ${RED}$ONLY_PYTHON${NC}"
echo -e "仅在 Java:      ${YELLOW}$ONLY_JAVA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 保存到项目目录
FINAL_REPORT="$PROJECT_ROOT/docs/plans/2026-03-03-backend-java-migration-verification/endpoint-diff.md"
cp "$REPORT_MD" "$FINAL_REPORT"
echo -e "${GREEN}✓ 报告已保存到: $FINAL_REPORT${NC}"
echo ""

# 询问是否查看完整报告
read -p "是否查看完整报告？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v less &> /dev/null; then
        less "$FINAL_REPORT"
    else
        cat "$FINAL_REPORT"
    fi
fi

echo ""
echo -e "${GREEN}完成！${NC}"
echo -e "临时文件已保存到 /tmp/，可以手动清理："
echo -e "  $PYTHON_JSON"
echo -e "  $JAVA_JSON"
echo -e "  $REPORT_MD"
echo -e "  $RESULT_JSON"
