resource "aws_cloudwatch_event_rule" "tigers_notify" {
  name                = "${var.project_name}-schedule"
  description         = "阪神タイガースの試合結果通知"
  schedule_expression = "cron(0 9 * * ? *)"
}

resource "aws_iam_role" "eventbridge_ecs" {
  name = "${var.project_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge_ecs" {
  role       = aws_iam_role.eventbridge_ecs.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_cloudwatch_event_target" "tigers_notify" {
  rule      = aws_cloudwatch_event_rule.tigers_notify.name
  target_id = "TigersNotifyECS"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.eventbridge_ecs.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.main.arn
    task_count          = 1
    launch_type         = "FARGATE"

    network_configuration {
      subnets          = [aws_subnet.public_1.id,aws_subnet.public_2.id]
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = true
    }
  }
}