FROM apify/actor-python:3.9

# Copy source code
COPY . ./

# Install dependencies
RUN pip install -r requirements.txt

# Run actor
CMD ["python", "main.py"]