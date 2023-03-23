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
    })
    d.addEventListener('dragend', (e) => {
      d.classList.remove('ahx-dragging')
    })
    d.addEventListener('dragover', (e) => {
      e.preventDefault()
      const dragged = E('.ahx-dragging')
      if (dragged == d) return
      const box = d.getBoundingClientRect()
      const mouseX = e.clientX
      //console.log(`>>>>>>> ${mouseX} ${box.right}`)
      if (mouseX + box.width / 2 > box.right) { 
        container.insertBefore( d, dragged)
      } else if (mouseX - box.width / 2 < box.left ) { 
        container.insertBefore( dragged, d)
      }
    }) // dragover
  }) // draggables.forEach()
} // setupDragging()


