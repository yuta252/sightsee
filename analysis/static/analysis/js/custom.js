// Difine JQuery except for AJAX

$(function() {
    // jQuery Upload Thumbs
    $('form input:file').uploadThumbs({
        position  : '#preview',    // any: arbitrarily jquery selector
    });
    $('form input:file').on('change', function(){
        $(this).next('#file_loader').remove();
        $(this).parents('.upload').hide();
    });
});


/*
$(function() {
    $("#comment-input").height(20);//init
    $("#comment-input").css("lineHeight","20px");//init

    $("#comment-input").on("input",function(evt){
        if(evt.target.scrollHeight > evt.target.offsetHeight){
            $(evt.target).height(evt.target.scrollHeight);
        }else{
            var lineHeight = Number($(evt.target).css("lineHeight").split("px")[0]);
            while (true){
                $(evt.target).height($(evt.target).height() - lineHeight);
                if(evt.target.scrollHeight > evt.target.offsetHeight){
                    $(evt.target).height(evt.target.scrollHeight);
                    break;
                }
            }
        }
    });
});


//signup form
$(function(){
    $('.signup-wrapper .form-control').focus(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #E38509');
        $(this).css('outline', 'none');
    });
    $('.signup-wrapper .form-control').blur(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #bbb');
    });
});

//comment input
$(function(){
    $('.post-form').focus(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #E38509');
    });
    $('.post-form').blur(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #bbb');
    });
});


//reply input
$(function(){
    $('.reply-form').focus(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #E38509');
    });
    $('.reply-form').blur(function(event){
        event.preventDefault();
        $(this).css('border', 'solid 2px #bbb');
    });
});

$(function() {
    $("#reply-input").height(20);//init
    $("#reply-input").css("lineHeight","20px");//init

    $("#reply-input").on("input",function(evt){
        if(evt.target.scrollHeight > evt.target.offsetHeight){
            $(evt.target).height(evt.target.scrollHeight);
        }else{
            var lineHeight = Number($(evt.target).css("lineHeight").split("px")[0]);
            while (true){
                $(evt.target).height($(evt.target).height() - lineHeight);
                if(evt.target.scrollHeight > evt.target.offsetHeight){
                    $(evt.target).height(evt.target.scrollHeight);
                    break;
                }
            }
        }
    });
});
*/