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

        $('.popup-menu-btn').click(function(){
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

        let project_filter_union = "";
        let project_filter_search = "";
        let project_filter_country = "";
        let project_filter_visibility = "";

        let filter_projects = function(union, search, country, visibility){
            console.log("Filter union:", union, "search: ", search, "country:", country, "visibility:", visibility);
            data = {};
            if(union) data['union'] = union;
            if(search) data['search'] = search;
            if(country) data['country'] = country;
            if(visibility) data['visibility'] = visibility;
            $.ajax({
                url: '/ajax/filter-projects/',
                data: data,
                dataType: 'html',
                success: function (data) {
                    console.log("success...", data)
                    let projects_list = $('#projects-list');
                    projects_list.children().fadeOut('fast');
                    projects_list.html(data);
                    projects_list.children().fadeIn('fast');
                },
                error: function(error){
                    console.log(error)
                }
            });
        };

        $('#search').find('.dropdown').dropdown(
            {
                onChange: function (value, text, choice) {
                    console.log(value);
                }
            }
        );

        $('#search').search(
            {
                type: 'category',
                selector:{
                  results: '.results',
                },
                searchOnFocus: true,
                transition: 'fade-in',
                apiSettings: {
                    url: '/ajax/search/{query}',
                    onResponse: function(results) {
                        console.log(results);
                    }
                },
                onSearchQuery: function (query) {
                    console.log(query);
                }
            }
        );

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

        $('#project-filter-clear').on('click', function() {
            $('#project-filter-countries').dropdown('clear');
            project_filter_country = "";
            $('#project-filter-hosts').dropdown('clear');
            project_filter_union = "";
            $('#news-filter-search').val('');
            project_filter_search = "";
            filter_projects(project_filter_union, project_filter_search, project_filter_country, project_filter_visibility);
        });

        $('#project-filter-hosts')
            .dropdown({
                onChange: function(value, text, choice){
                    project_filter_union = value;
                    filter_projects(project_filter_union,
                        project_filter_search,
                        project_filter_country,
                        project_filter_visibility);
                },
            });

        $('#project-filter-countries')
            .dropdown({
                onChange: function(value, text, choice){
                    project_filter_country = value;
                    filter_projects(project_filter_union,
                        project_filter_search,
                        project_filter_country,
                        project_filter_visibility);
                },
            });

        $('#project-filter-search').on("change paste keyup", function() {
            project_filter_search = $(this).val();

            console.log(project_filter_search)
            filter_projects(project_filter_union,
                project_filter_search,
                project_filter_country,
                project_filter_visibility);
        });
    });

