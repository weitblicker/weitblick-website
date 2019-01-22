  $(document)
    .ready(function() {

      // fix menu when passed
      $('.masthead')
        .visibility({
          once: false,
          onBottomPassed: function() {
            $('.fixed.menu').transition('fade in');
          },
          onBottomPassedReverse: function() {
            $('.fixed.menu').transition('fade out');
          }
        })
      ;

      // create sidebar and attach to menu open
      /*$('.ui.sidebar')
        .sidebar('attach events', '.toc.item')
      ;*/

      $('#popup-menu-btn').click(function(){
       // $('#popup-menu.show').css('height', $('#popup-menu').first().height());
        $('#popup-menu').slideToggle();
      });

      $('.ui.search').search({
          apiSettings: {
              url: '/ajax/search/{query}'
          },
          type: 'category',
          minCharacters: 3,
      });

      var news_filter = "";

      $('#news-filter.ui.dropdown')
        .dropdown({
          allowAdditions: true,
          onChange: function(value, text, choice){
            console.log(value, text);
            $.ajax({
              url: '/ajax/filter-news/',
              data: {
                'union': value,
              },
              dataType: 'html',
              success: function (data) {
                $('#news-list').html(data)
                console.log(data)
              },
              error: function(error){
                console.log(error)
              }
            });
          },
      });

    });

