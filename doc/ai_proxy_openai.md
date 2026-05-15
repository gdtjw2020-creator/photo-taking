部署详情：
技术栈：使用 Docker 容器化运行（ginuerzh/gost），开启了 --restart always，服务器重启后会自动恢复。
服务端口：10880 (TCP)
认证信息：
用户名：tangstudio
密码：PhotoAI2026Gate
转发链路：外网 10880 (带加密) -> 本地 40001 (WARP) -> Cloudflare 节点。
您需要做的操作：
开放端口：请在 AWS 控制台的 Security Group（安全组） 中，添加入站规则，允许 TCP 10880 端口（来源可以设为 0.0.0.0/0，因为我们已经有强密码保护了）。
配置 Railway： 在 Railway 的环境变量 AI_PROXY 中填写以下地址：
socks5://tangstudio:PhotoAI2026Gate@13.211.161.113:10880
验证情况：
底层通畅：我已确认您服务器上的 40001 (WARP) 工作正常，能成功获取到 Cloudflare 的 IP (104.28.228.20)。
网关已就绪：gost 服务已在后台运行并监听 10880 端口。