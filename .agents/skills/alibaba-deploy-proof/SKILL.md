---
name: alibaba-deploy-proof
description: Automates deployment to Alibaba Cloud Function Compute / ECS and generates the mandatory proof recording and logs for the Qwen Hackathon submission.
---

# Alibaba Cloud Deployment & Proof Skill

To qualify for the hackathon prizes, the project **must** be deployed on Alibaba Cloud infrastructure and we must provide concrete proof of this deployment. This skill standardizes the deployment and proof generation pipeline to ensure no points are lost on technicalities.

## 1. Deployment Target Options
- **Option A (Preferred): Function Compute (FC)** - Serverless deployment of the LangGraph FastAPI backend. Best for scale and minimal maintenance.
- **Option B: ECS (Elastic Compute Service)** - Standard VM deployment via Docker Compose. Use this if the MCP servers (like Postgres) need to be co-located with the agents.

## 2. Infrastructure as Code (IaC)
All deployments must be scriptable. 
- Use the `aliyun` CLI tool.
- Ensure all environment variables (`DASHSCOPE_API_KEY`, `GOOGLE_MAPS_API_KEY`, `POSTGRES_URL`) are injected securely via Alibaba Cloud Secret Manager or FC environment config.

## 3. Proof Artifact Generation Workflow
When executing this skill, perform the following steps automatically:
1. **Health Check**: Ping the deployed endpoint (e.g., `https://<alibaba-url>/api/health`) and verify a 200 OK response.
2. **End-to-End Test**: Send a complex synthetic errand scenario to the deployed orchestrator and wait for the final negotiated plan.
3. **Log Extraction**: Pull the last 50 lines of logs from Alibaba Cloud demonstrating the DashScope API calls being made from the cloud IP.
4. **Generate Output**: Create a file named `ALIBABA_CLOUD_PROOF.md` in the repository root containing:
   - The public endpoint URL.
   - The successful cURL request/response trace.
   - The snippet of the Alibaba Cloud dashboard (or CLI output) confirming the resource exists.
   - The extracted execution logs.

## 4. Execution Command
```bash
# Example script structure
./scripts/deploy_and_prove.sh --target ecs --region cn-hangzhou
```
