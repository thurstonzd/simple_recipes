// from https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#Examples
const input = document.querySelector('input[type="file"]');

const preview = document.querySelector('.preview');

const dropArea = document.querySelector('#drop-area');

// add event listeners for drag-and-drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

dropArea.addEventListener('drop', handleDrop, false);

// define drag-and-drop handlers
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dropArea.classList.add('highlight');
}

function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

function handleDrop(e) {
    input.files = e.dataTransfer.files;
    updateImageDisplay();
}

input.addEventListener('change', updateImageDisplay);

// code to update images displayed
function updateImageDisplay() {
    while (preview.firstChild) {
        preview.removeChild(preview.firstChild);
    }
    
    const curFiles = input.files;
    if (curFiles.length === 0) {
        const para = document.createElement('p');
        para.textContent = 'No files currently selected for upload.';
        preview.appendChild(para);
    } else {
        const list = document.createElement('ol');
        const text_array = []
        const text_box = document.querySelector(
            "#images_content textarea");
        preview.appendChild(list);
        
        for (const file of curFiles) {
            const listItem = document.createElement('li');
            const para = document.createElement('p');
            
            para.textContent = `File name ${file.name}, file size ${returnFileSize(file.size)},`;
            const image = document.createElement('img');
            image.src = URL.createObjectURL(file);
            
            listItem.appendChild(image);
            listItem.appendChild(para);
            
            list.appendChild(listItem);
            
            text_array.push(file.name);
        }
        
        newline = String.fromCharCode(13, 10);
        text_box.value = text_array.join(newline);
    }
}

function returnFileSize(number) {
    if (number < 1024) {
        return number + 'bytes';
    } else if (number >= 1024 && number < 1048576) {
        return (number/1024).toFixed(1) + 'KB';
    } else if (number >= 1048576) {
        return (number/1048576).toFixed(1) + 'MB';
    }
}