resource "aws_eks_cluster" "main" {
  name     = "eks-project-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.23"

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id,
      aws_subnet.public_a.id,
      aws_subnet.public_b.id
    ]
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "eks-project-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  instance_types = ["t3.medium"]
}

