odoo.define('bi_car_repair_management.car_request', function (require) {
'use strict';
	var ajax = require('web.ajax');

	$(document).ready(function() {

     	if($('#product_id') != null){
			
			$('#product_id').on('change',function(event) {
				event.stopPropagation();
	        	event.preventDefault();
				var car_id = this.value;

				ajax.jsonRpc('/action/send', 'call', {'car_id':car_id}).then(function(request_data)
					{
						var data = JSON.parse(request_data);
						$('#model').val(data.model_id);
						$('#brand').val(data.brand_id);
						$('#year').val(data.year);						
					});
			});
		}
    });
});