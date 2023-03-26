'use strict;'

const ROWLEN = 3

// Enable correct buttons if an edit happened
//---------------------------------------------
function editHappened(edit_type) {
  if (edit_type == 'select_pic') {
    if (A('.ahx-selected').length > 0) {
      E('#btn_del').disabled = false
      E('#btn_save').disabled = true
    } else {
      E('#btn_del').disabled = true
      E('#btn_save').disabled = !editHappened.flag
    }
  } // select_pic
  else if (edit_type == 'edit_caption' || edit_type == 'pic_moved' ) {
    editHappened.flag = true
    E('#btn_del').disabled = true
    var selected = A('.ahx-selected')
    selected.forEach( x => { x.classList.remove( 'ahx-selected') })
    if (E('#btn_del').disabled) {
      E('#btn_save').disabled = false
    } else {
      E('#btn_save').disabled = true
    }
  } // edit_caption

  E('#btn_revert').disabled = true
  if (editHappened.flag || A('.ahx-selected').length > 0) { E('#btn_revert').disabled = false }
} // editHappened()
editHappened.flag = false

// Event handlers for the pic caption textareas
//------------------------------------------------
function setupCaptionHandlers() {
  var tas = A('.ahx-ta')
  tas.forEach( t => {
    t.addEventListener( 'input', ev => {
      editHappened('edit_caption')
    })
  }) // forEach 
} // setupCaptionHandlers()

// Pictures get a red frame if selected by click
//---------------------------------------------------
function setupSelect() {
  var pics = A('.ahx-pic')
  pics.forEach( p => { 
    p.addEventListener( 'click', ev => {
      var target = ev.target
      // Maybe the image wasn't clicked => get it.
      if (target.tagName == 'DIV') { target = ev.target.children[0] }
      // Mark/unmark pic as selected
      var classes = [... target.classList]
      if (classes.includes( 'ahx-selected')) {
        target.classList.remove( 'ahx-selected')
      } else {
        target.classList.add( 'ahx-selected')
      }
      // Store list of marked pics in hidden form input #marked_pic_ids
      const marked = A('.ahx-selected').reduce( (acc, curr) => { return acc.concat(curr.id) }, [] )
      E('#marked_pic_ids').value = JSON.stringify(marked)
      editHappened( 'select_pic')
    })
  }) // forEach 
} // setupSelect()

// Pictures can be reordered by drag and drop
//-----------------------------------------------
function setupDragging() {

  //------------------------------------------
  function startScrolling(draggedElement) {
    const scrollSize = 100 // px
    const scrollInterval = 50 // ms
    setupDragging.scrollTimer = setInterval(() => {
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
      // Scroll up
      } else if (elementRect.top < topThreshold && viewportTop > 0) { 
        window.scrollBy(0, -scrollSize) // Scroll the page by scrollSize pixels
      } 
    }, scrollInterval)
  } // startScrolling()

  //-------------------------------------------
  function stopScrolling() {
    clearInterval( setupDragging.scrollTimer)
    setupDragging.scrollTimer = null
  }

  // Compute or retrieve row and col of pics.
  // Note that pic_id is prefixed with 'pic_'.
  //-------------------------------------------
  function rowcol( action, pic_id) {
    if (action == 'compute') {
      // Compute and remember row and col for all pics
      const pics = document.querySelectorAll( '.ahx-pic') 
      var idx = 0
      pics.forEach( p => {
        rowcol.lookup[p.id] = [ Math.floor( idx / ROWLEN), idx % ROWLEN, idx ] 
        idx++
      })
    } else if (action == 'get') {
      // Retrieve row,col for one pic
      return rowcol.lookup[pic_id]
    }
    return [0,0,0]
  } // rowcol()
  rowcol.lookup = {}

  const container = E('.ahx-container')

  // There is a snap back animation on drag end which we don't want.
  //  e.preventDefault() on document.dragover prevents it.
  document.addEventListener('dragover', (e) => {
    e.preventDefault()
  })

  var draggables = A('.ahx-draggable')
  draggables.forEach( d => {
    d.addEventListener('dragstart', (e) => {
      rowcol('compute')
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
      const [target_row,target_col,target_idx] = rowcol( 'get', d.children[0].id )
      const [source_row,source_col,source_idx] = rowcol( 'get', dragged.children[0].id )
      const box = d.getBoundingClientRect()
      const mouseX = e.clientX
      // If dragging to right edge, insert after the target d
      if (mouseX + box.width / 4 > box.right && 
          ( (target_col == ROWLEN - 1) || (target_idx == draggables.length - 1 ))) 
      { 
        if (target_row < source_row) return
        container.insertBefore( d, dragged)
        //console.log('>>>>>>>> right')
        editHappened( 'pic_moved')
        rowcol('compute')
      } else { // Main case
        //if (target_idx == source_idx+1 && target_idx < draggables.length - 1) return
        if (target_row > source_row && target_col == 0) return
        container.insertBefore( dragged, d)
        //console.log('>>>>>>>> left')
        editHappened( 'pic_moved')
        rowcol('compute')
      }
    }) // dragover
  }) // draggables.forEach()
} // setupDragging()
setupDragging.scrollTimer = null
