// MQTT Broker connection details - assumes mqtt is on same host as webserver
const broker = location.hostname;
const clientId = 'webpage-layout-' + Math.random().toString(16).substr(2, 8);

// MQTT client setup
var client = new Paho.Client(broker, Number(9001), clientId);
if(client) {
 client.onConnectionLost = onConnectionLost;
 client.onMessageArrived = onMessageArrived;

 // Connect to the broker
 client.connect({
  onSuccess: onConnect,
  keepAliveInterval: 60, // Keep alive interval in seconds
  onFailure: onFailure
 });
} else {
 console.error('Cannot connect to MQTT server');
}

function onConnect() {
 console.log('Connected to MQTT broker');
 // Subscribe to all messages
 client.subscribe('#');
}
function onFailure(responseObject) {
    console.log('Failed to connect: ' + responseObject.errorMessage);
}

function onConnectionLost(responseObject) {
 if (responseObject.errorCode !== 0) {
  console.log('Connection lost: ' + responseObject.errorMessage);
 }
}

function updateDynamicValue(dynamicCellId, dynamicValue) {
 const dynamicCell = document.getElementById(dynamicCellId);
 if (dynamicCell) {
   dynamicCell.textContent = dynamicValue;
   let cssClasses = dynamicCell.className || '';
   cssClasses = cssClasses.replace(/state_([^ ]*)/g, ''); // Remove any existing state
   cssClasses += " state_" + dynamicValue;
   if(dynamicValue != 0) {
    cssClasses += " state_true";
   }
   dynamicCell.className = cssClasses.replace(/,/g, ' state_');
 }
 // Popout area may have one with a _pop suffix
 const dynamicCell_pop = document.getElementById(dynamicCellId + '_pop');
 if (dynamicCell_pop) {
   dynamicCell_pop.textContent = dynamicValue;
 }
 
 checkRoutesSet();
}

function checkRoutesSet() {
 // This is not overly clean, it iterates through all section "Route Set" _routeset elements
 // and determines which routes are set.
 let routesFound = {};
 for (const [key, value] of Object.entries(oLayoutData.Sections)) {
  let elem = document.getElementById(key + '_routeset_pop');
  if(elem) {
   routesFound[elem.innerText] = key;
  }
 }
 // Map of routes set determined
 
 // Mark routes that are set
 for (const [key, value] of Object.entries(oLayoutData.Routes)) {
  let lblElem = document.getElementById(key + '_route');
  let sectionElem = document.getElementById(key + '_section');
  if(lblElem && sectionElem) {
   if(routesFound[key] != null) {
    lblElem.classList.add('_set');
    sectionElem.innerText = routesFound[key];
   } else {
    lblElem.classList.remove('_set');
    sectionElem.innerText = '';
   }
  }
 }
}

function onMessageArrived(message) {
  console.log('Received message: ' + message.payloadString);
  const topicParts = message.destinationName.split('/');
  const currentAttributeKey = topicParts[topicParts.length - 1];
  const currentAssetKey = topicParts[topicParts.length - 2];
  console.log(currentAssetKey+"_"+currentAttributeKey, message.payloadString)
  updateDynamicValue(currentAssetKey+"_"+currentAttributeKey, message.payloadString);
  displayMessage(message.payloadString);
}

function displayMessage(message) {
  const messagesDiv = document.getElementById('messages');
  // Too big
  // messagesDiv.innerHTML += '<p>' + message + '</p>';
}

function publishMessage(payload, message) {
  console.log(payload, message)
  const messageObject = new Paho.Message(message);
  messageObject.destinationName = payload; // Replace with your MQTT topic
  client.send(messageObject);
}

// Function to create buttons dynamically within a group
function createButtonsInSection(sectionName, data) {
 const oContainer = document.getElementById('container');

 for (const [key, value] of Object.entries(data)) {

   // Buttons based on the section type
   if (sectionName == "Signals") {
     const oPopout = createMarker(oContainer, key, "_aspect", value, "signal", sectionName);
     
     addStatusCell(oPopout, "Aspect", key+"_aspect");
     addButtonCell(oPopout, "Danger", `${sectionName.toLowerCase()}_${key.toLowerCase()}_danger`, () => publishMessage(`set/signal/${key}`, 'danger'), value.dangerreg);
     addButtonCell(oPopout, "Clear", `${sectionName.toLowerCase()}_${key.toLowerCase()}_clear`, () => publishMessage(`set/signal/${key}`, 'clear'), value.clearreg);
     addButtonCell(oPopout, "Caution", `${sectionName.toLowerCase()}_${key.toLowerCase()}_caution`, () => publishMessage(`set/signal/${key}`, 'caution'), value.cautionreg);
     addButtonCell(oPopout, "Calling On", `${sectionName.toLowerCase()}_${key.toLowerCase()}_callingon`, () => publishMessage(`set/signal/${key}`, 'associated_position_light'), value.callingonreg);
     addButtonCell(oPopout, "Shunt", `${sectionName.toLowerCase()}_${key.toLowerCase()}_shunt`, () => publishMessage(`set/signal/${key}`, 'position_light'), value.callingonreg);
   } else if (sectionName == "Points") {
     const oPopout = createMarker(oContainer, key, "_set_direction", value, "point", sectionName);
     
     addStatusCell(oPopout, "Direction", key+"_set_direction");
     addStatusCell(oPopout, "Detection", key+"_detection_status");
     addButtonCell(oPopout, "Normal", `${sectionName.toLowerCase()}_${key.toLowerCase()}_normal`, () => publishMessage(`set/point/${key}`, 'normal'));
     addButtonCell(oPopout, "Reverse", `${sectionName.toLowerCase()}_${key.toLowerCase()}_reverse`, () => publishMessage(`set/point/${key}`, 'reverse'));
   } else if (sectionName == "Sections") {
     const oPopout = createMarker(oContainer, key, "_occstatus", value, "section", sectionName);
     
     // buttons for Sections
     addStatusCell(oPopout, "Occupancy", key+"_occstatus");
     addStatusCell(oPopout, "Route Set", key+"_routeset");
     addButtonCell(oPopout, "Clear", `${sectionName.toLowerCase()}_${key.toLowerCase()}_clear`, () => publishMessage(`set/section/${key}/occstatus`, '0'));
     addButtonCell(oPopout, "Occupy", `${sectionName.toLowerCase()}_${key.toLowerCase()}_occupy`, () => publishMessage(`set/section/${key}/occstatus`, '1'));
   } else if (sectionName == "Plungers") {
     const oPopout = createMarker(oContainer, key, "_plunger", value, "plunger", sectionName);
     
     // Buttons for Plungers
     addButtonCell(oPopout, "Press", `${sectionName.toLowerCase()}_${key.toLowerCase()}_press`, () => publishMessage(`set/plunger/${key}`, '1'));
   } else if (sectionName == "Routes") {
     const oRouteTbl = document.getElementById('routetable');
     const oRow = document.createElement('tr');
     oRouteTbl.appendChild(oRow);
     
     const lblCell = document.createElement('td');
     lblCell.innerHTML = key + "<br><div class='_desc'>" + value.description + "</div>";
     lblCell.id = key + "_route";
     oRow.appendChild(lblCell);
     
     const section = document.createElement('td');
     section.id = key + "_section";
     section.className = '_section';
     oRow.appendChild(section);
     
     const btnCell = document.createElement('td');
     oRow.appendChild(btnCell);
     // Buttons for Set and Clear for Routes
     addButtonCell(btnCell, "Set", `${sectionName.toLowerCase()}_${key.toLowerCase()}_set`, () => publishMessage(`set/route/${key}`, 'True'));
     addButtonCell(btnCell, "Clear", `${sectionName.toLowerCase()}_${key.toLowerCase()}_clear`, () => publishMessage(`set/route/${key}`, 'False'));
   }
 }
}

/**
 * createMarker - creates a HTML marker on the overlay at coords specified in value.coords
 *
 * @param oContainer : DOM container element
 * @param key : string key from JSON
 * @param keysuffix : specific attribute from MQTT to use on marker
 * @param value : data from JSON for this key
 * @param type : string type (for CSS)
 * @param sectionName : the type of MQTT data
 *
 * @return oPopout : DOM popout area to add buttons to
 */
function createMarker(oContainer, key, keysuffix, value, type, sectionName) {
  const oCb = document.createElement('input');
  oCb.type = 'radio';
  oCb.name = 'taptarget'; // All the same group
  oCb.className = '_cb';
  oCb.id = key + keysuffix + "_cb";
  oCb.innerText = key;
  oContainer.appendChild(oCb);
  
  const oMarker = document.createElement('label');
  oMarker.className = '_item _' + type + ' ' + ((value.coords && value.coords.dir) ? value.coords.dir : '');
  oMarker.id = key + keysuffix;
  oMarker.htmlFor = oCb.id;
  // Position
  if(value.coords) {
   oMarker.style.left = value.coords.x + "%";
   oMarker.style.top = value.coords.y + "%";
   oMarker.style.transform = "rotate(" + (value.coords.rotate || 0) + "deg)";
  }
  oContainer.appendChild(oMarker);
  
  // Create buttons popout
  const oPopout = document.createElement('div');
  oPopout.className = '_popout';
  oContainer.appendChild(oPopout);
  
  const oPopoutLabel = document.createElement('label');
  oPopoutLabel.className = '_popoutlbl';
  oPopoutLabel.innerHTML = "<span class='_key'>" + sectionName + ": " + key + "</span><br>" + value.description;
  oPopout.appendChild(oPopoutLabel);
  
  return oPopout;
}

function addStatusCell(oParent, text, id) {
  const container = document.createElement('div');
  container.className = "_container";
  oParent.appendChild(container);
  
  const label = document.createElement('div');
  label.textContent = text;
  label.className = "_status_label";
  container.appendChild(label);
  
  const value = document.createElement('div');
  value.textContent = "Loading ...";
  value.className = "_status_value";
  value.id = id + "_pop";
  container.appendChild(value);
}

function addButtonCell(oParent, text, id, clickHandler, isVisible) {
 if (isVisible === undefined || isVisible) { // Check if isVisible is defined
  const button = document.createElement('button');
  button.textContent = text;
  button.id = id;
  button.addEventListener("click", clickHandler);
  oParent.appendChild(button);
 }
}

let oLayoutData;
function gotJSON(jsonData) {
 oLayoutData = jsonData;
	// Create buttons for Signals, Points, and Routes in separate sections
	createButtonsInSection('Points', jsonData.Points);
 createButtonsInSection('Sections', jsonData.Sections);
	createButtonsInSection('Signals', jsonData.Signals);
 createButtonsInSection('Routes', jsonData.Routes);
 createButtonsInSection('Plungers', jsonData.Plungers);
}

$.getJSON("default.json", function(json) {
 console.log(json); // this will show the info it in firebug console
 gotJSON(json);
})

// Point locator finder, dumps coords to console
document.addEventListener("DOMContentLoaded", function(event) {
    const container = document.getElementById('container');
    container.addEventListener('click', (e) => {
        const rect = container.getBoundingClientRect();
        const xPercent = ((e.clientX - rect.left) / rect.width) * 100;
        const yPercent = ((e.clientY - rect.top) / rect.height) * 100;
        console.log(`X: ${xPercent.toFixed(2)}%, Y: ${yPercent.toFixed(2)}%`);
    });
});

function togglefs() {
	window.isfullscreen = window.isfullscreen || 0;
	if(window.isfullscreen) {
		closeFullScreen();
		window.isfullscreen = 0;
	} else {
		openFullScreen();
		window.isfullscreen = 1;
	}
}

function openFullScreen() {
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    } else if (document.documentElement.mozRequestFullScreen) { // Firefox
        document.documentElement.mozRequestFullScreen();
    } else if (document.documentElement.webkitRequestFullscreen) { // Chrome, Safari, and Opera
        document.documentElement.webkitRequestFullscreen();
    } else if (document.documentElement.msRequestFullscreen) { // IE/Edge
        document.documentElement.msRequestFullscreen();
    }
}

function closeFullScreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.mozCancelFullScreen) { // Firefox
        document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) { // Chrome, Safari, and Opera
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) { // IE/Edge
        document.msExitFullscreen();
    }
}