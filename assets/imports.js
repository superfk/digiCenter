let fs = require('fs');

// const links = document.querySelectorAll('link[rel="import"]')

const links = ['sections/config.html','sections/seqEditor.html','sections/run.html']

// Import and add each page to the DOM
Array.prototype.forEach.call(links, (link) => {
  // let template = link.import.querySelector('.task-template')
  fs.readFile(link, (err, html) => {
    if (err){
      console.error(err)
    }else {
      parser = new DOMParser();
      doc = parser.parseFromString(html, "text/html")
      let template = doc.querySelector('.task-template')
      let clone = document.importNode(template.content, true)
      document.querySelector('.content').appendChild(clone)
    }
  })
})