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

        let news_filter_union = "";
        let news_filter_search = "";
        let news_filter_archive = "";

        let filter_news = function(union, search, archive){
            console.log("Filter:", union, search, archive);
            data = {};
            if(union) data['union'] = union;
            if(search) data['search'] = search;
            if(archive) data['archive'] = archive;
            $.ajax({
                url: '/ajax/filter-news/',
                data: data,
                dataType: 'html',
                success: function (data) {
                    let news_list = $('#news-list');
                    news_list.children().fadeOut('fast');
                    news_list.html(data);
                    news_list.children().fadeIn('fast');
                },
                error: function(error){
                    console.log(error)
                }
            });
        };

        $('#news-filter-clear').on('click', function() {
            $('#news-filter-archive').dropdown('clear');
            news_filter_archive = "";
            $('#news-filter-hosts').dropdown('clear');
            news_filter_union = "";
            $('#news-filter-search').val('');
            news_filter_search = "";
            filter_news(news_filter_union, news_filter_search, news_filter_archive);
        });

        $('#news-filter-archive')
            .dropdown({
                allowCategorySelection: true,
                onChange: function(value, text, choice){
                    news_filter_archive = value;
                    console.log(value, text, choice);
                    filter_news(news_filter_union, news_filter_search, news_filter_archive);
                },
            });

        $('#news-filter-hosts')
            .dropdown({
                onChange: function(value, text, choice){
                    news_filter_union = value;
                    filter_news(news_filter_union, news_filter_search, news_filter_archive);
                },
            });

        $('#news-filter-search').on("change paste keyup", function() {
            news_filter_search = $(this).val();
            filter_news(news_filter_union, news_filter_search, news_filter_archive);
        });
    });

