# Getting Started with Co-DETR API

This guide provides step-by-step instructions for setting up and using the Co-DETR object detection API. It's designed for beginners with little to no technical background.

## What is Co-DETR?

Co-DETR is an advanced object detection model that can identify and locate multiple objects in images. This API allows you to upload images and receive results with detected objects highlighted.

## Prerequisites

Before getting started, you need to install:

1. **Docker Desktop** - To run the API without complex setup
2. **Git** - To download the project code
3. **Postman** (optional) - For easily testing the API

### Installing Docker Desktop

1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Run the installer and follow the prompts
3. After installation, start Docker Desktop from your Start menu
4. Wait until Docker is running (the whale icon in taskbar will stop animating)
5. Verify installation by opening Command Prompt and typing:
   ```
   docker --version
   ```

### Installing Git (Optional)

Git is only needed if you prefer to clone the repository instead of downloading it as a ZIP file.

1. Download Git from [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Run the installer and follow the default installation options
3. Verify installation by opening Command Prompt (search "cmd" in Start menu) and typing:
   ```
   git --version
   ```

### Installing Postman (Optional)

1. Download Postman from [https://www.postman.com/downloads/](https://www.postman.com/downloads/)
2. Run the installer and follow the prompts
3. After installation, open Postman from your Start menu

## Step 1: Download the Co-DETR Project

### Option A: Download as ZIP (Recommended for beginners)

1. Go to the Co-DETR repository at [https://github.com/KShervington/Co-DETR](https://github.com/KShervington/Co-DETR)
2. Click the green "Code" button
3. Select "Download ZIP" from the dropdown menu
4. Save the ZIP file to your computer (e.g., to Downloads folder)
5. Right-click the downloaded ZIP file and select "Extract All..."
6. Choose a location to extract the files (e.g., Documents folder)
7. Click "Extract" to unzip the files
8. Open the extracted "Co-DETR-main" folder

### Option B: Using Git

1. Open Command Prompt
2. Navigate to the directory where you want to download the project (e.g., Documents):
   ```
   cd C:\Users\YourUsername\Documents
   ```
3. Clone the repository:
   ```
   git clone https://github.com/KShervington/Co-DETR.git
   ```
4. Navigate into the project folder:
   ```
   cd Co-DETR
   ```

## Step 2: Download the Model File

The model file is too large to be included in the repository, so you need to download it separately.

1. Download the Co-DETR model file, `pytorch_model.pth`, from [this link](https://huggingface.co/zongzhuofan/co-detr-vit-large-coco/tree/main)
2. Place the downloaded model file in the root directory of the Co-DETR project

## Step 3: Build and Run the Docker Container

1. Make sure Docker Desktop is running
2. Open Command Prompt in the Co-DETR directory
3. Build the Docker image (this may take several minutes):
   ```
   docker build -f Dockerfile.api -t codetr-api .
   ```
4. Run the Docker container:
   ```
   docker run -p 8000:8000 -v ./checkpoints:/app/checkpoints codetr-api
   ```
5. Wait until you see a message indicating the server is running
6. Keep this window open while using the API

## Step 4: Prepare Test Images

1. Create a folder on your computer for test images (e.g., `C:\Users\YourUsername\Pictures\test-images`)
2. Find or download some images with objects you want to detect (people, cars, animals, etc.)
3. Save these images in your test images folder

## Step 5: Use the API

### Option 1: Using Postman

1. Open Postman
2. Create a new request:
   - Click "New" → "Request"
   - Name it "Co-DETR Detect"
   - Save to a collection (create a new one if needed)
3. Set up your request:
   - Set request type to "POST" using the dropdown
   - Enter URL: `http://localhost:8000/detect`
   - Go to "Body" tab
   - Select "form-data"
   - Add a key called "image" and set its type to "File"
   - Click "Select Files" and choose one of your test images
4. Send the request by clicking the blue "Send" button
5. The response will include an image with detected objects highlighted

### Option 2: Using a Web Browser

1. Open your browser and go to: `http://localhost:8000/docs`
2. This opens the FastAPI documentation page
3. Find the `/detect` endpoint and click "Try it out"
4. Upload your image using the file selector
5. Click "Execute" to send the request
6. Download and view the result from the response

## Understanding the Results

The API will return an image with colored boxes around detected objects. Each box includes:

- The object type (person, car, dog, etc.)
- A confidence score (how certain the model is about the detection)

## Troubleshooting

### Docker Issues

- **"Docker not running" error**: Make sure Docker Desktop is open and running
- **Port already in use**: If port 8000 is already used by another application, change the port mapping in the docker run command (e.g., `-p 8001:8000`)

### API Issues

- **Slow response**: Detection may take longer on larger images or slower computers
- **Error during detection**: Ensure your model file is correctly placed in the checkpoints folder
- **File format errors**: Try using JPEG or PNG images if other formats don't work

## Additional Resources

- [Co-DETR GitHub Repository](https://github.com/YourUsername/Co-DETR)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Need Help?

If you encounter any issues not covered in this guide, please contact your instructor or teaching assistant for assistance.
