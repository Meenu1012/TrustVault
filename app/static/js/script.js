
document.addEventListener("DOMContentLoaded", function () {

    const fileInput = document.getElementById("document-file");
    const fileName = document.getElementById("file-name");

    if (fileInput && fileName) {

        fileInput.addEventListener("change", function () {

            if (fileInput.files.length > 0) {
                fileName.textContent = fileInput.files[0].name;
            } else {
                fileName.textContent = "No file selected";
            }

        });

    }

});
