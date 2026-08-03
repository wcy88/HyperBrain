# Tasks

- [x] Task 1: 检查并准备本地 Git 仓库
  - [x] SubTask 1.1: 检查项目根目录是否存在 `.git`
  - [x] SubTask 1.2: 若不存在则执行 `git init`
  - [x] SubTask 1.3: 检查并配置 `.gitignore`，排除敏感文件与构建产物

- [x] Task 2: 整理待提交文件并创建提交
  - [x] SubTask 2.1: 查看当前 git status 与 diff
  - [x] SubTask 2.2: 确认不会提交 `config.yaml`、数据库、缓存等敏感文件
  - [x] SubTask 2.3: 暂存有效变更并创建 conventional commit

- [x] Task 3: 创建或复用 GitHub 远程仓库
  - [x] SubTask 3.1: 检查当前 remote 配置
  - [x] SubTask 3.2: 若未配置 remote，通过 GitHub MCP/CLI 创建仓库 `HyperBrain`
  - [x] SubTask 3.3: 将 remote 地址配置为本地仓库

- [ ] Task 4: 推送并验证
  - [x] SubTask 4.1: 重试 git push（本地到 GitHub 443 连接失败，已重试 10 次）
  - [x] SubTask 4.2: 通过 GitHub MCP 推送 README、.gitignore、发布脚本并验证
  - [ ] SubTask 4.3: 完成完整代码推送（待用户提供 GitHub Token 后运行 scripts/push_to_github.py）

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3
