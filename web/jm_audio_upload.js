import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Function to preview the audio file
function previewAudio(node, file) {
  // Remove existing preview widgets
  while (node.widgets.length > 2) {
    node.widgets.pop();
  }
  
  // Remove existing audio element if any
  try {
    var el = document.getElementById("JM_AudioPreview");
    if (el) el.remove();
  } catch (error) {
    console.log(error);
  }
  
  // Create audio preview element
  var element = document.createElement("div");
  element.id = "JM_AudioPreview";
  const previewNode = node;
  
  // Add a DOM widget for the audio preview
  var previewWidget = node.addDOMWidget("audiopreview", "preview", element, {
    serialize: false,
    hideOnZoom: false,
    getValue() {
      return element.value;
    },
    setValue(v) {
      element.value = v;
    },
  });
  
  // Compute size for the widget
  previewWidget.computeSize = function (width) {
    if (this.aspectRatio && !this.parentEl.hidden) {
      let height = (previewNode.size[0] - 20) / this.aspectRatio + 10;
      if (!(height > 0)) {
        height = 0;
      }
      this.computedHeight = height + 10;
      return [width, height];
    }
    return [width, -4]; // No loaded src, widget should not display
  };
  
  // Set up widget properties
  previewWidget.value = { hidden: false, paused: false, params: {} };
  previewWidget.parentEl = document.createElement("div");
  previewWidget.parentEl.className = "audio_preview";
  previewWidget.parentEl.style["width"] = "100%";
  element.appendChild(previewWidget.parentEl);
  
  // Create audio element
  previewWidget.audioEl = document.createElement("audio");
  previewWidget.audioEl.controls = true;
  previewWidget.audioEl.loop = false;
  previewWidget.audioEl.muted = false;
  previewWidget.audioEl.style["width"] = "100%";
  
  // Listen for metadata loading
  previewWidget.audioEl.addEventListener("loadedmetadata", () => {
    previewWidget.aspectRatio = 4; // Default aspect ratio for audio controls
  });
  
  // Listen for errors
  previewWidget.audioEl.addEventListener("error", () => {
    previewWidget.parentEl.hidden = true;
    console.error("Error loading audio preview");
  });

  // Set parameters for the audio view
  let params = {
    filename: file,
    type: "input",
  };

  // Set visibility and autoplay
  previewWidget.parentEl.hidden = previewWidget.value.hidden;
  previewWidget.audioEl.autoplay = !previewWidget.value.paused && !previewWidget.value.hidden;
  
  // Set the audio source
  previewWidget.audioEl.src = api.apiURL("/view?" + new URLSearchParams(params));
  previewWidget.audioEl.hidden = false;
  previewWidget.parentEl.appendChild(previewWidget.audioEl);
}

// Function to handle audio upload
function audioUpload(node, inputName, inputData, app) {
  // Find the audio path widget
  const audioWidget = node.widgets.find((w) => w.name === "audio_path");
  let uploadWidget;
  
  // Get default value
  var default_value = audioWidget.value;
  
  // Define getter/setter for audio_path
  Object.defineProperty(audioWidget, "audio_path", {
    set: function (value) {
      this._real_value = value;
    },
    get: function () {
      let value = "";
      if (this._real_value) {
        value = this._real_value;
      } else {
        return default_value;
      }

      if (value.filename) {
        let real_value = value;
        value = "";
        if (real_value.subfolder) {
          value = real_value.subfolder + "/";
        }
        value += real_value.filename;
        if (real_value.type && real_value.type !== "input")
          value += ` [${real_value.type}]`;
      }
      return value;
    },
  });
  
  // Function to upload a file
  async function uploadFile(file, updateNode, pasted = false) {
    try {
      // Wrap file in formdata so it includes filename
      const body = new FormData();
      body.append("image", file);
      if (pasted) body.append("subfolder", "pasted");
      
      // Send the upload request
      const resp = await api.fetchApi("/upload/image", {
        method: "POST",
        body,
      });

      if (resp.status === 200) {
        const data = await resp.json();
        // Add the file to the dropdown list and update the widget value
        let path = data.name;
        if (data.subfolder) path = data.subfolder + "/" + path;

        if (!audioWidget.options.values.includes(path)) {
          audioWidget.options.values.push(path);
        }

        if (updateNode) {
          audioWidget.value = path;
          previewAudio(node, path);
        }
      } else {
        alert(resp.status + " - " + resp.statusText);
      }
    } catch (error) {
      alert(error);
    }
  }

  // Create file input element
  const fileInput = document.createElement("input");
  Object.assign(fileInput, {
    type: "file",
    accept: "audio/mpeg, audio/wav, audio/x-m4a",
    style: "display: none",
    onchange: async () => {
      if (fileInput.files.length) {
        await uploadFile(fileInput.files[0], true);
      }
    },
  });
  document.body.append(fileInput);

  // Create the button widget for selecting files
  uploadWidget = node.addWidget(
    "button",
    "Upload Audio",
    "Audio",
    () => {
      fileInput.click();
    }
  );

  uploadWidget.serialize = false;

  // Preview the current audio file
  previewAudio(node, audioWidget.value);
  
  // Override callback to update preview when selection changes
  const cb = node.callback;
  audioWidget.callback = function () {
    previewAudio(node, audioWidget.value);
    if (cb) {
      return cb.apply(this, arguments);
    }
  };

  return { widget: uploadWidget };
}

// Register our custom widget
ComfyWidgets.JMAUDIOUPLOAD = audioUpload;

// Register extension
app.registerExtension({
  name: "JM.MiniMax.AudioUpload",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData?.name == "JM_LoadAudio") {
      // This will be processed by the ComfyWidgets
      nodeData.input.optional = nodeData.input.optional || {};
      nodeData.input.optional.upload = ["JMAUDIOUPLOAD"];
    }
  },
}); 