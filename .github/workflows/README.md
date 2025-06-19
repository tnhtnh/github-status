# GitHub Incident Visualizer Workflow

This directory contains the GitHub Action workflow for automatically generating GitHub incident visualizations.

## Workflow File: `generate-visualization.yml`

### Purpose

This workflow automates the process of fetching GitHub incident data, processing it, and generating a visualization showing incidents by severity over time.

### Trigger Events

- **Scheduled**: Runs automatically on the 1st day of each month (`0 0 1 * *`)
- **Manual**: Can be triggered manually using the `workflow_dispatch` event

### Workflow Steps

1. **Checkout Repository**: Clones the repository code
2. **Set up Python**: Configures Python 3.11 environment
3. **Install Dependencies**: Installs required packages from `requirements.txt`
4. **Generate Visualization**: Runs the main script to create the visualization
5. **Upload Artifact**: Saves the visualization as a workflow artifact
6. **Create Output Directory**: Ensures the output directory exists
7. **Copy Visualization**: Copies the visualization to the output directory
8. **Commit and Push**: Commits the new visualization to the repository

### Testing the Workflow

To test this workflow:

1. **Local Testing**:
   - Run the main script locally to ensure it works as expected:
     ```bash
     python src/main.py --output incidents-visualization.png
     ```
   - Verify the visualization is generated correctly

2. **GitHub Testing**:
   - Push the workflow file to GitHub
   - Go to the Actions tab in your repository
   - Manually trigger the workflow using the "Run workflow" button
   - Monitor the workflow execution
   - Verify the artifact is generated and uploaded
   - Check that the visualization is committed to the output directory

### Troubleshooting

If the workflow fails:

1. Check the workflow logs for error messages
2. Verify that all dependencies are correctly specified in `requirements.txt`
3. Ensure the main script accepts the `--output` parameter
4. Check repository permissions for the GitHub Action