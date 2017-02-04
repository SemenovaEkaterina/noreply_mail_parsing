$(function() {
    $('.mail_parsing-accept').on('click', function(event) {
        var id = $(this).attr('message_id');
        event.preventDefault();

        $.ajax({
            headers: { "X-CSRFToken": $('[name=csrfmiddlewaretoken]').val()},
            url: "/accept/",
            type: 'POST',
            data: {
                'id': id
            },
            success: function (data) {
                if(data.status == 'OK') {
                    $('.mail_parsing-accept').addClass('btn-success');
                    $('.mail_parsing-not_accept').removeClass('btn-danger');
                }
            }
        });
    });


    $('.mail_parsing-not_accept').on('click', function(event) {
        var id = $(this).attr('message_id');
        event.preventDefault();

        $.ajax({
            headers: { "X-CSRFToken": $('[name=csrfmiddlewaretoken]').val()},
            url: "/not_accept/",
            type: 'POST',
            data: {
                'id': id
            },
            success: function (data) {
                if(data.status == 'OK') {
                    $('.mail_parsing-not_accept').addClass('btn-danger');
                    $('.mail_parsing-accept').removeClass('btn-success');
                }
            }
        });
    });

});
