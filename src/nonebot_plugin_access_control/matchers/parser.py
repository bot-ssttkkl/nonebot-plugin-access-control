from nonebot.rule import ArgumentParser

parser = ArgumentParser(prog="rbac")
subparsers = parser.add_subparsers(help="子命令", required=True, dest="subcommand")

# ==== subject ====
subject_parser = subparsers.add_parser("subject", help="主体管理")
subject_parser.add_argument("subject", help="主体")
subject_subparsers = subject_parser.add_subparsers(help="操作", required=True, dest="action")

#     ==== subject <xxx> ls ====
subject_ls_parser = subject_subparsers.add_parser("ls", help="列出主体可用服务")

#     ==== subject <xxx> remove <xxx> ====
subject_remove_parser = subject_subparsers.add_parser("remove", help="为主体移除服务的权限设置")
subject_remove_parser.add_argument("service", help="服务")

#     ==== subject <xxx> allow <xxx> ====
subject_allow_parser = subject_subparsers.add_parser("allow", help="为主体启用服务")
subject_allow_parser.add_argument("service", help="服务")

#     ==== subject <xxx> deny <xxx> ====
subject_deny_parser = subject_subparsers.add_parser("deny", help="为主体禁用服务")
subject_deny_parser.add_argument("service", help="服务")

# ==== service ====
service_parser = subparsers.add_parser("service", help="主体管理")
service_parser.add_argument("service", help="主体")
service_subparsers = service_parser.add_subparsers(help="操作", required=True, dest="action")

#     ==== service <xxx> ls ====
service_ls_parser = service_subparsers.add_parser("ls", help="列出服务的主体权限设置")
