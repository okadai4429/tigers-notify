resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project_name}"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "${var.project_name}"
    image = "${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}:latest"
    environment = [{
      name  = "SLACK_WEBHOOK_URL"
      value = var.slack_webhook_url
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
        "awslogs-create-group"  = "true"
      }
    }
  }])
}

resource "aws_security_group" "ecs_tasks" {
  name   = "${var.project_name}-ecs-sg"
  vpc_id = aws_vpc.main.id

  # アウトバウンド（全許可）
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"  # 全プロトコル
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-ecs-sg" }
}