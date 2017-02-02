$(function() {
    $('.mail_parsing-accept').on('click', function(event) {
        var id = $(this).attr('message_id');
        $(this).addClass('btn btn-success');

        event.preventDefault();

        $.ajax({
            url: "/accept/",
            type: 'POST',
            data: {
                'id': id
            },
            success: function (data) {
                console.log('1');
            }
        });
    });
});
