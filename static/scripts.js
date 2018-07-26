// Execute when the DOM is fully loaded
$(document).ready(function() {
     $(".ex_button").click(function(e) {

        let parameters = {
            exercise: $(this).val()
        };

        $.getJSON("/button_pressed", parameters, function(data, textStatus, jqXHR) {

            contentString = '<ul class="list-group id=ex_list">';
            if (data.length !== 0) {
                data.forEach(function(row) {
                    contentString += '<li class="list-group-item"><div class="row"><div class="col">' + row.name + '</div>' +
                    '<div class="col">' + row.t + '</div></div></li>';
                });
            } else {
                contentString = 'No Exercises';
            }
            contentString += '</ul>';

            $("#exlist > ul").replaceWith(contentString);

        });

    });

});
