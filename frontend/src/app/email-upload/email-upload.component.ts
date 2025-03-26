import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-email-upload',
  templateUrl: './email-upload.component.html',
  styleUrls: ['./email-upload.component.css'],
})
export class EmailUploadComponent {
  selectedFile: File | null = null;
  responseData: any;
  formattedResponse: string = '';
  isLoading: boolean = false;

  constructor(private http: HttpClient) {}

  // Handle file selection
  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  // Upload and process the file
  onUpload() {
    if (!this.selectedFile) {
      alert('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    // Show loading indicator
    this.isLoading = true;

    // Send the file to Flask API
    this.http.post<any>('http://127.0.0.1:5000/validate', formData).subscribe(
      (response) => {
        console.log(response);
        this.responseData = response.result.result;

        // Hide loading indicator after success
        this.isLoading = false;
      },
      (error) => {
        console.error('Error uploading file:', error);
        alert('Error processing the file. Please try again.');

        // Hide loading indicator after error
        this.isLoading = false;
      }
    );
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file && file.name.endsWith('.eml')) {
      this.selectedFile = file;
    }
  }

  triggerFileInput() {
    const fileInput = document.getElementById('fileInput') as HTMLInputElement;
    fileInput.click();
  }
}
