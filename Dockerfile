FROM python
EXPOSE 8000
WORKDIR /myapplication
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
