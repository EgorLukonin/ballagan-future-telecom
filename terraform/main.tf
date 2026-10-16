resource "openstack_compute_keypair_v2" "generated_key" {
  name       = var.ssh_key_name
  public_key = file("${path.module}/id_rsa.pub")
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
  region   = var.region
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
  flavor_name     = var.flavor_name
  key_pair        = openstack_compute_keypair_v2.generated_key.name
  security_groups = []

  lifecycle {
    ignore_changes = [
      security_groups,
    ]
  }

  block_device {
    uuid                  = data.openstack_images_image_v2.ubuntu.id
    source_type           = "image"
    destination_type      = "volume"
    volume_size           = var.volume_size
    volume_type           = "basic.ru-9a"
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

data "openstack_networking_floatingip_v2" "fip" {
  address = var.selectel_ip_address
}

resource "openstack_networking_floatingip_associate_v2" "fip_assoc" {
  floating_ip = data.openstack_networking_floatingip_v2.fip.address
  port_id     = openstack_networking_port_v2.vm_port.id

  depends_on = [
    openstack_networking_router_interface_v2.router_interface,
    openstack_compute_instance_v2.vm
  ]
}