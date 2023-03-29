'use strict;'

const ROWLEN = 3

// Catch 'btn_up','btn_down' and handle in js without submitting the form
//---------------------------------------------------------------------------
function setupForm() {
  const form = E('#frm_pics')
  form.addEventListener("submit", function(ev) {
    if (! ['btn_up','btn_down'].includes(ev.submitter.id)) return
    ev.preventDefault()
    const container = E('.ahx-container')
    var draggables = A('.ahx-draggable')
    var selected = A('.ahx-selected')
    
    if (ev.submitter.id == 'btn_down') {
      selected.reverse().forEach( e => {
        const dragged = e.parentElement.parentElement
        const nnext = dragged.nextElementSibling
        if (nnext != null) {
          container.insertBefore( nnext, dragged)
          editHappened('pic_moved')
        }
      })
    } else { // up
      selected.forEach( e => {
        const dragged = e.parentElement.parentElement
        const previous = dragged.previousElementSibling
        if (previous != null) {
          container.insertBefore( dragged, previous)
          editHappened('pic_moved')
        }
      })      
    } // up
  }) // addEventListener()
} // setupForm()

//-------------------------
function clearFlash() {
  var flash = E('#flash_msg')
  if (flash) {
    flash.innerHTML = ''
  }
} // clearFlash()

// Enable correct buttons if an edit happened
//---------------------------------------------
function editHappened(edit_type) {
  if (edit_type == 'select_pic') {
    if (A('.ahx-selected').length > 0) {
      E('#btn_del').disabled = false
      E('#btn_save').disabled = true
      if (E('#btn_up') != null) {
        E('#btn_up').disabled = false
        E('#btn_down').disabled = false
      }
    } else {
      E('#btn_del').disabled = true
      E('#btn_save').disabled = !editHappened.flag
      if (E('#btn_up') != null) {
        E('#btn_up').disabled = true
        E('#btn_down').disabled = true
      }
    }
  } // select_pic
  else if (edit_type == 'edit_caption' || edit_type == 'pic_moved' ) {
    editHappened.flag = true
    E('#btn_del').disabled = true
    if (E('#btn_up') != null) {
      E('#btn_up').disabled = true
      E('#btn_down').disabled = true
    }
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
  const D = setupDragging
  draggables.forEach( d => {
    if (isMobile()) {
      setupMobile(d)
    } else {
      setupDesktop(d)
    } // dragging on mobile device
  })
  
  //----------------------------
  function setupDesktop(d) {
    // Dragging on desktop
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
        editHappened( 'pic_moved')
        rowcol('compute')
      } else { // Main case
        if (target_row > source_row && target_col == 0) return
        container.insertBefore( dragged, d)
        editHappened( 'pic_moved')
        rowcol('compute')
      }
    }) // dragover
  } // setupDesktop(d) 

  // Dragging on mobile device
  //------------------------------
  function setupMobile(d) {
    // Just couldn't get this to work. Too bad.
    return
  } // setupMobile

} // setupDragging()
