js_do_everything = """
        async (images_selected_state, multi_select_ckbx_state) => {
          const gallery = document.querySelector("#gallery_id")
          const buttons_thumbnails = gallery.querySelectorAll(".thumbnails > button");
          const buttons_large = gallery.querySelectorAll(".grid-container > button");
          buttons_thumbnails.forEach((btn, idx) => {
            if(images_selected_state.includes(idx)){
              btn.classList.add('selected-custom');
            }else{
              btn.classList.remove('selected-custom');
            }
            btn.classList.remove('selected');
          })
          buttons_large.forEach((btn, idx) => {
            if(images_selected_state.includes(idx)){
              btn.classList.add('selected-custom');
            }else{
              btn.classList.remove('selected-custom');
            }
          })
          const elements = document.querySelectorAll('*[class^="preview"], *[class*=" preview"]');
          elements.forEach(element => {
            if (multi_select_ckbx_state[0]) {
              element.style.display = 'none';
            } else {
              element.style.display = '';
              element.style.removeProperty('display');
            }
          })
          return images_selected_state
        }
        """


