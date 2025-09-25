variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "ecfr-agency-size"
}

variable "suffix" {
  type    = string
  default = "dev"
}

variable "ecfr_base_url" {
  type    = string
  default = "https://www.ecfr.gov"
}

variable "ecfr_title_json_path_tmpl" {
  type    = string
  default = "/api/versioner/v1/full/{date}/title-{title}.json"
}

variable "http_user_agent" {
  type    = string
  default = "ecfr-agency-size-lambda/1.0"
}

variable "ecfr_max_titles" {
  type    = number
  default = 50
}
