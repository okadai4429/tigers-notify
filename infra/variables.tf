variable "aws_region" {
  description = "AWSのリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "account_id" {
  description = "AWS アカウント ID"
  type        = string
  default     = "570934198023"
}

variable "project_name" {
  description = "プロジェクト名"
  type        = string
  default     = "tigers-notify"
}

variable "slack_webhook_url" {
  description = "Slack の Webhook URL"
  type        = string
  sensitive   = true
  default     = ""
}