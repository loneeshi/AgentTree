#!/bin/bash
# CoreGPU DeepSeek-R1 API 环境变量设置脚本
# 运行方式: source setup_coregpu.sh

echo "🚀 设置 CoreGPU DeepSeek-R1 API 环境变量"
echo "================================"

# 请将下面的 YOUR_API_KEY 替换为你的实际 API Key
export DPSK_API_KEY="sk-Ty3U2Cr3hibXi8CEvnUVkgwudd1mEIf6syBXyQdxadoWfpbz"

# 设置 CoreGPU 相关配置
export LLM_PROVIDER="coregpu"
export LLM_MODEL="DeepSeek-R1"
# 注意：base_url 只到 /v1，不包含 /chat/completions
# OpenAI SDK 会自动添加 /chat/completions
export LLM_BASE_URL="https://ai.api.coregpu.cn/v1"

# 启用 LLM 提取功能
export ENABLE_LLM_EXTRACTION="true"

# 可选：启用流式输出（用于调试，可以看到模型思考过程）
# export ENABLE_LLM_STREAMING="true"

echo "✅ 环境变量设置完成："
echo "  DPSK_API_KEY: ${DPSK_API_KEY:0:10}..." 
echo "  LLM_PROVIDER: $LLM_PROVIDER"
echo "  LLM_MODEL: $LLM_MODEL"
echo "  LLM_BASE_URL: $LLM_BASE_URL"
echo "  ENABLE_LLM_EXTRACTION: $ENABLE_LLM_EXTRACTION"
echo ""
echo "💡 使用方法："
echo "  1. 编辑此文件，设置你的真实 API Key"
echo "  2. 运行: source setup_coregpu.sh"
echo "  3. 测试: python kg_builder/llm_relation_extractor.py"
echo ""
echo "🎯 DeepSeek-R1 特性："
echo "  - 支持思考推理过程（reasoning）"
echo "  - 启用流式输出可观察模型思考过程"
echo "  - 使用 JSON 格式确保结构化输出"
