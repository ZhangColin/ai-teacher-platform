"""内置支持的模型提供商和模型定义"""

# 内置供应商定义
BUILTIN_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "description": "DeepSeek AI 模型"
    },
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "description": "OpenAI 模型"
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "default_base_url": "https://api.moonshot.cn/v1",
        "description": "Moonshot AI 模型"
    },
    "glm": {
        "name": "智谱 AI",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "description": "智谱 AI 大模型"
    },
}

# 内置模型定义
BUILTIN_MODELS = {
    "deepseek": {
        "deepseek-chat": {
            "name": "DeepSeek Chat",
            "capabilities": ["chat"],
            "description": "DeepSeek 对话模型"
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "capabilities": ["chat"],
            "description": "DeepSeek 代码模型"
        },
    },
    "openai": {
        "gpt-4": {
            "name": "GPT-4",
            "capabilities": ["chat"],
            "description": "OpenAI GPT-4"
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "capabilities": ["chat", "image"],
            "description": "OpenAI GPT-4o"
        },
    },
    "kimi": {
        "moonshot-v1-8k": {
            "name": "Moonshot v1 8K",
            "capabilities": ["chat"],
            "description": "Kimi 对话模型"
        },
    },
    "glm": {
        "glm-4": {
            "name": "GLM-4",
            "capabilities": ["chat"],
            "description": "智谱 GLM-4"
        },
        "glm-4-voice": {
            "name": "GLM-4 Voice",
            "capabilities": ["audio"],
            "description": "智谱语音合成"
        },
        "cogview-4": {
            "name": "CogView-4",
            "capabilities": ["image"],
            "description": "智谱图像生成"
        },
        "cogvideox": {
            "name": "CogVideoX",
            "capabilities": ["video"],
            "description": "智谱视频生成"
        },
    },
}

# 能力类型定义
CAPABILITY_TYPES = {
    "chat": "文字对话",
    "image": "图片生成",
    "audio": "音频生成",
    "video": "视频生成",
}

# 所有能力的列表
ALL_CAPABILITIES = list(CAPABILITY_TYPES.keys())


def get_builtin_providers():
    """获取内置供应商列表"""
    return [
        {
            "code": code,
            "name": config["name"],
            "default_base_url": config["default_base_url"],
            "description": config.get("description", "")
        }
        for code, config in BUILTIN_PROVIDERS.items()
    ]


def get_builtin_models(provider_code: str = None):
    """获取内置模型列表"""
    if provider_code:
        models = BUILTIN_MODELS.get(provider_code, {})
        return [
            {
                "code": model_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            }
            for model_code, config in models.items()
        ]

    # 返回所有模型
    result = []
    for provider_code, models in BUILTIN_MODELS.items():
        for model_code, config in models.items():
            result.append({
                "code": model_code,
                "provider_code": provider_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            })
    return result


def validate_provider_code(provider_code: str) -> bool:
    """验证供应商代码是否有效"""
    return provider_code in BUILTIN_PROVIDERS


def validate_model_code(provider_code: str, model_code: str) -> bool:
    """验证模型代码是否有效"""
    if provider_code not in BUILTIN_MODELS:
        return False
    return model_code in BUILTIN_MODELS[provider_code]