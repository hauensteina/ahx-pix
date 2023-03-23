'use strict;'

// Pictures get a red frame if selected by click
//---------------------------------------------------
function setupSelect() {
  var pics = A('.ahx-pic')
  pics.forEach( p => { 
    p.addEventListener( 'click', ev => {
      // Mark/unmark pic as selected
      var classes = [... ev.target.classList]
      if (classes.includes( 'ahx-selected')) {
        ev.target.classList.remove( 'ahx-selected')
      } else {
        ev.target.classList.add( 'ahx-selected')
      }
      // Enable/disable delete button
      E('#btn_del').disabled = true
      if (A('.ahx-selected').length > 0) {
        E('#btn_del').disabled = false
      }
      // Store list of marked pics in hidden form input #marked_pic_ids
      const marked = A('.ahx-selected').reduce( (acc, curr) => { return acc.concat(curr.id) }, [] )
      E('#marked_pic_ids').value = JSON.stringify(marked)
    })
  }) 
} // setupSelect()

// Pictures can be reordered by drag and drop
//-----------------------------------------------
function setupDragging() {

  //----------------------------------------
  function startScrolling(draggedElement) {
    const scrollSize = 100
    setupDragging.scrollInterval = setInterval(() => {
      // Define the threshold where the auto-scroll should start 
      const bottomThreshold = window.innerHeight * 0.9 
      const topThreshold = window.innerHeight * 0.1 
      // Get the position of the dragged element
      const elementRect = draggedElement.getBoundingClientRect()
      // Get the position of the bottom of the viewport
      const viewportBottom = window.scrollY + window.innerHeight 
      // Get the position of the top of the viewport
      const viewportTop = window.scrollY
      // Scroll down
      if (elementRect.bottom > bottomThreshold && viewportBottom < document.body.scrollHeight) { 
        window.scrollBy(0, scrollSize) // Scroll the page by scrollSize pixels
      }
      // Scroll up
      else if (elementRect.top < topThreshold && viewportTop > 0) { 
        window.scrollBy(0, -scrollSize) // Scroll the page by scrollSize pixels
      }
    }, 50)
  } // startScrolling()

  //----------------------------------------
  function stopScrolling() {
    clearInterval( setupDragging.scrollInterval)
  }

  //const draggables = A('.ahx-draggable')
  const container = E('.ahx-container')

  // There is a snap back animation on drag end which we don't want.
  //  e.preventDefault() on document.dragover prevents it.
  document.addEventListener('dragover', (e) => {
    e.preventDefault()
  })

  A('.ahx-draggable').forEach( d => {
    d.addEventListener('dragstart', (e) => {
      d.classList.add('ahx-dragging')
      startScrolling(d)
    })
    d.addEventListener('dragend', (e) => {
      d.classList.remove('ahx-dragging')
      stopScrolling()
    })
    d.addEventListener('dragover', (e) => {
      e.preventDefault()
      const dragged = E('.ahx-dragging')
      if (dragged == d) return
      const box = d.getBoundingClientRect()
      const mouseX = e.clientX
      //console.log(`>>>>>>> ${mouseX} ${box.right}`)
      if (mouseX + box.width / 4 > box.right) { 
        container.insertBefore( d, dragged)
        //} else if (mouseX - box.width / 2.1 < box.left ) { 
      } else { 
        container.insertBefore( dragged, d)
      }
    }) // dragover
  }) // draggables.forEach()
} // setupDragging()
setupDragging.scrollInterval = null

