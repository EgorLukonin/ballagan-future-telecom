resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "openstack_compute_keypair_v2" "generated_key" {
  name       = "auto-key"
  public_key = tls_private_key.ssh.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/id_rsa"
  file_permission = "0600"
}

resource "openstack_networking_network_v2" "net" {
  name           = "Ballagan-network"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "subnet" {
  name       = "Ballagan-subnet"
  network_id = openstack_networking_network_v2.net.id
  cidr       = "192.168.0.0/24"
  ip_version = 4
  gateway_ip = "192.168.0.1"
}

data "openstack_networking_network_v2" "external" {
  external = true
  region   = "ru-6"
}

resource "openstack_networking_router_v2" "router" {
  name                = "router-Ballagan-network"
  admin_state_up      = true
  external_network_id = data.openstack_networking_network_v2.external.id
}

resource "openstack_networking_router_interface_v2" "router_interface" {
  router_id = openstack_networking_router_v2.router.id
  subnet_id = openstack_networking_subnet_v2.subnet.id
}

resource "openstack_networking_port_v2" "vm_port" {
  name       = "custom-port"
  network_id = openstack_networking_subnet_v2.subnet.network_id

  depends_on = [
    openstack_networking_router_interface_v2.router_interface
  ]
}

data "openstack_images_image_v2" "ubuntu" {
  name        = "Ubuntu 24.04 LTS 64-bit"
  most_recent = true
}

resource "openstack_compute_instance_v2" "vm" {
  name            = "ballagan-server"
  flavor_name     = "SL2.2-4096-AMD"
  key_pair        = openstack_compute_keypair_v2.generated_key.name
  security_groups = ["default"]

  lifecycle {
    ignore_changes = [
      security_groups,
    ]
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.ubuntu.id
    source_type           = "image"
    destination_type      = "volume"
    volume_size           = 20
    boot_index            = 0
    delete_on_termination = true
  }

  network {
    port = openstack_networking_port_v2.vm_port.id
  }

  depends_on = [
    openstack_networking_subnet_v2.subnet,
    openstack_networking_router_interface_v2.router_interface,
    openstack_networking_port_v2.vm_port
  ]
}

resource "openstack_networking_floatingip_v2" "fip" {
  pool = data.openstack_networking_network_v2.external.name
}

resource "openstack_networking_floatingip_associate_v2" "fip_assoc" {
  floating_ip = openstack_networking_floatingip_v2.fip.address
  port_id     = openstack_networking_port_v2.vm_port.id

  depends_on = [
    openstack_networking_router_interface_v2.router_interface,
    openstack_compute_instance_v2.vm
  ]
}