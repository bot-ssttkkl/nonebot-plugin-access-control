from nonebot.rule import ArgumentParser

parser = ArgumentParser(prog="rbac")
subparsers = parser.add_subparsers(help="子命令", dest="subcommand")

# ==== help ====
help_parser = subparsers.add_parser("help", help="帮助")

# ==== permission ====
permission_parser = subparsers.add_parser("permission", help="权限")
permission_subparsers = permission_parser.add_subparsers(help="操作", dest="action", required=True)

permission_allow_parser = permission_subparsers.add_parser("allow", help="为主体启用服务")
permission_allow_parser.add_argument("--sbj", "--subject", help="主体", dest="subject", required=True)
permission_allow_parser.add_argument("--srv", "--service", help="服务", dest="service", required=True)

permission_deny_parser = permission_subparsers.add_parser("deny", help="为主体禁用服务")
permission_deny_parser.add_argument("--sbj", "--subject", help="主体", dest="subject", required=True)
permission_deny_parser.add_argument("--srv", "--service", help="服务", dest="service", required=True)

permission_rm_parser = permission_subparsers.add_parser("rm", help="为主体删除服务权限配置")
permission_rm_parser.add_argument("--sbj", "--subject", help="主体", dest="subject", required=True)
permission_rm_parser.add_argument("--srv", "--service", help="服务", dest="service", required=True)

permission_ls_parser = permission_subparsers.add_parser("ls", help="列出已配置的权限")
permission_ls_parser.add_argument("--sbj", "--subject", help="主体", dest="subject")
permission_ls_parser.add_argument("--srv", "--service", help="服务", dest="service")

# ==== limit ====
limit_parser = subparsers.add_parser("limit", help="限流")
limit_subparsers = limit_parser.add_subparsers(help="操作", dest="action", required=True)

limit_add_parser = limit_subparsers.add_parser("add", help="为主体与服务添加限流规则（按照用户限流）")
limit_add_parser.add_argument("--sbj", "--subject", help="主体", dest="subject", required=True)
limit_add_parser.add_argument("--srv", "--service", help="服务", dest="service", required=True)
limit_add_parser.add_argument("--lim", "--limit", help="次数", dest="limit", required=True)
limit_add_parser.add_argument("--span", help="时间间隔", dest="span", required=True)

limit_rm_parser = limit_subparsers.add_parser("rm", help="删除限流规则")
limit_rm_parser.add_argument("id", help="规则ID")

limit_ls_parser = limit_subparsers.add_parser("ls", help="列出已配置的限流规则")
limit_ls_parser.add_argument("--sbj", "--subject", help="主体", dest="subject")
limit_ls_parser.add_argument("--srv", "--service", help="服务", dest="service")

limit_reset_parser = limit_subparsers.add_parser("reset", help="重置限流计数")

# ==== service ====
service_parser = subparsers.add_parser("service", help="服务")
service_subparsers = service_parser.add_subparsers(help="操作", dest="action", required=True)

service_ls_parser = service_subparsers.add_parser("ls", help="列出服务与子服务层级")
service_ls_parser.add_argument("--srv", "--service", help="服务", dest="service")
