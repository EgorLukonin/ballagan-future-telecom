variable "selectel_username" {
  type        = string
}

variable "selectel_password" {
  type        = string
  sensitive   = true
}

variable "selectel_account" {
  type        = string
}

variable "project_id" {
  type        = string
}

variable "selectel_ip_address" {
  type        = string
  default     = null
}

variable "flavor_name" {
  type        = string
  default     = "SL1.2-4096"
}

variable "volume_size" {
  type        = number
  default     = 20
}

variable "volume_type" {
  type        = string
  default     = "fast.ru-9a"
}

variable "ssh_key_name" {
  type        = string
  default     = "auto-key"
}

variable "region" {
  type        = string
  default     = "ru-9"
}