# AI Key File / AI密钥文件

Commodity Lab can import an AI key file from any folder. This is intended for test distribution: install the Windows client, place the key file anywhere on the local machine, then open `Settings` from the lower-left menu and choose `Import AI key file`.

Commodity Lab 支持从任意文件夹导入 AI密钥文件。测试分发时，先安装 Windows 客户端，再把密钥文件放在本机任意位置，打开左下角 `设置`，选择 `导入 AI密钥文件`。

## Security / 安全要求

- Do not commit real API keys to this repository.
- Do not paste real API keys into release notes, screenshots, logs, or GitHub issues.
- The imported key is used only on the local machine at runtime.

- 不要把真实 API Key 提交到仓库。
- 不要在 release notes、截图、日志或 GitHub issue 里暴露真实 API Key。
- 导入后的密钥只在本机运行时使用。

## JSON Format / JSON 格式

Only `provider` and `api_key` are required. Legacy `model` and `base_url` fields may remain in old sample files, but Commodity Lab ignores them for the final runtime route.

只需要 `provider` 和 `api_key`。旧密钥文件里可以保留 `model` 和 `base_url` 字段，但 Commodity Lab 最终运行时会忽略这些字段，由程序固定匹配模型和地址。

```json
{
  "provider": "haineng",
  "api_key": "REPLACE_WITH_TEST_KEY"
}
```

DeepSeek fallback/testing profile:

```json
{
  "provider": "deepseek",
  "api_key": "REPLACE_WITH_TEST_KEY"
}
```

Legacy files are still accepted:

```json
{
  "provider": "haineng",
  "api_key": "REPLACE_WITH_TEST_KEY",
  "model": "DeepSeek-V4",
  "base_url": "http://old-or-local-url.example/v1"
}
```

## Key-Value Format / 键值格式

```text
provider=haineng
api_key=REPLACE_WITH_TEST_KEY
```

`.env` style files and Python-style quoted assignments are also accepted:

```text
PROVIDER="deepseek"
API_KEY="REPLACE_WITH_TEST_KEY"
```

OpenAI-compatible Python SDK samples are accepted when they contain `api_key`. `base_url` and `model` may exist in the sample, but Commodity Lab only uses them as provider hints and then applies its fixed runtime route:

```python
from openai import OpenAI

client = OpenAI(
    api_key="REPLACE_WITH_TEST_KEY",
    base_url="https://api.deepseek.com",
)

model = "deepseek-v4-flash"
```

A single-line file containing only the key is accepted. In that case Commodity Lab uses the provider currently selected in Settings.

也支持 `.env` 风格文件、Python 引号变量，以及 OpenAI 兼容 SDK 示例文件。若文件只有一行密钥，Commodity Lab 会使用设置页当前选择的供应方。

Supported provider aliases include `haineng`, `海能`, `deepseek`, and `ds`. Model aliases in old files are ignored for the final route.
