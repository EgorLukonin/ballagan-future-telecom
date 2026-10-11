output "server_ip" {
  value = data.openstack_networking_floatingip_v2.fip.address
}

resource "local_file" "ansible_inventory" {
  content  = <<-EOT
    [webservers]
    ${data.openstack_networking_floatingip_v2.fip.address} ansible_user=root ansible_ssh_private_key_file=${path.module}/id_rsa
  EOT
  filename = "${path.module}/hosts.ini"
}