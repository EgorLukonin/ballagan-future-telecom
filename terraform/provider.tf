provider "selectel" {
  domain_name = var.selectel_account
  username    = var.selectel_username
  password    = var.selectel_password
  auth_region = "ru-6a"
  auth_url    = "https://cloud.api.selcloud.ru/identity/v3/"
}

provider "openstack" {
  auth_url    = "https://cloud.api.selcloud.ru/identity/v3/"
  domain_name = var.selectel_account
  tenant_id   = var.project_id
  user_name   = var.selectel_username
  password    = var.selectel_password
  region      = "ru-6"
}