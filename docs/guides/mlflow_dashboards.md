# MLflow Dashboard Setup Guide for ATLAS

This guide provides instructions on how to set up and configure dashboards within the MLflow UI to monitor the performance and cost of your ATLAS multi-agent system.

## Accessing the MLflow UI

Ensure your MLflow Tracking Server is running. If you are using the `docker-compose.yml` provided in this project, you can typically access the UI at:

`http://localhost:5000`

## Creating a New Dashboard

1.  **Navigate to the Experiments Page:** Once in the MLflow UI, click on "Experiments" in the left sidebar.
2.  **Select Runs:** Choose the runs you want to include in your dashboard. You can filter runs by experiment name (e.g., `ATLAS_Task_*`), tags (e.g., `atlas.team`, `atlas.agent_type`), or parameters.
3.  **Create a Chart:**
    *   Select the runs you want to visualize.
    *   Click the "Charts" tab.
    *   Click "Create Chart".

## Recommended Charts for ATLAS Monitoring

Here are some recommended charts to create to gain insights into your ATLAS system:

### 1. Agent Cost Over Time

*   **Chart Type:** Line Chart
*   **X-Axis:** `step` (or `timestamp` if available and preferred)
*   **Y-Axis:** `metrics.final_cost_usd`
*   **Group By:** `params.model_name` or `tags.atlas.agent_type`
*   **Purpose:** Visualize the cost incurred by different models or agent types over the course of a task or across multiple runs.

### 2. Token Usage Distribution

*   **Chart Type:** Bar Chart or Pie Chart
*   **X-Axis:** (None for Pie, or `params.model_name` for Bar)
*   **Y-Axis:** `metrics.total_tokens`
*   **Group By:** `params.model_name` or `tags.atlas.agent_type`
*   **Purpose:** Understand which models or agents consume the most tokens.

### 3. Error Rate by Agent Type

*   **Chart Type:** Bar Chart
*   **X-Axis:** `tags.atlas.agent_type`
*   **Y-Axis:** Count of runs where `tags.status` is `FAILED`
*   **Purpose:** Identify which agent types are most prone to errors.
    *   *Note:* This requires custom aggregation or filtering in MLflow. You might need to export data and analyze externally for complex error rate calculations.

### 4. Model Provider Cost Comparison

*   **Chart Type:** Bar Chart
*   **X-Axis:** `params.model_provider`
*   **Y-Axis:** `metrics.final_cost_usd` (sum or average)
*   **Purpose:** Compare the total or average cost across different LLM providers.

### 5. Agent Performance Metrics (e.g., Quality Score)

*   **Chart Type:** Line Chart
*   **X-Axis:** `step`
*   **Y-Axis:** `metrics.quality_score`
*   **Group By:** `tags.atlas.agent_type` or `params.model_name`
*   **Purpose:** Track the quality of agent outputs over time or compare quality across different agents/models.

## Saving and Sharing Dashboards

MLflow allows you to save your chart configurations. Look for options to save or export your charts once you've configured them to your liking. You can also share links to specific runs or experiments.

## Advanced Monitoring

For more advanced monitoring and custom dashboards, consider integrating MLflow with external tools like Grafana, which can pull metrics directly from MLflow's backend database.