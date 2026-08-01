terraform {
  backend "s3" {
    bucket = "tigers-notify-tfstate-429"
    key    = "tigers-notify/terraform.tfstate"
    region = "ap-northeast-1"
  }
}