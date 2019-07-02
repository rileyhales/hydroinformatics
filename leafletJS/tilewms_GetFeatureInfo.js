L.TileLayer.WMFS = L.TileLayer.WMS.extend({
    onAdd: function (map) {
        L.TileLayer.WMS.prototype.onAdd.call(this, map);
        map.on('click', this.GetFeatureInfo, this);
    },
    onRemove: function (map) {
        L.TileLayer.WMS.prototype.onRemove.call(this, map);
        map.off('click', this.GetFeatureInfo, this);
    },

    GetFeatureInfo: function (evt) {
        if (document.getElementById('map').style.cursor === 'pointer') {
            // Construct a GetFeatureInfo request URL given a point
            let point = this._map.latLngToContainerPoint(evt.latlng, this._map.getZoom());
            let size = this._map.getSize();
            let params = {
                request: 'GetFeatureInfo',
                service: 'WMS',
                srs: 'EPSG:4326',
                version: this.wmsParams.version,
                format: this.wmsParams.format,
                bbox: this._map.getBounds().toBBoxString(),
                height: size.y,
                width: size.x,
                layers: this.wmsParams.layers,
                query_layers: this.wmsParams.layers,
                info_format: 'application/json'
            };
            params[params.version === '1.3.0' ? 'i' : 'x'] = point.x;
            params[params.version === '1.3.0' ? 'j' : 'y'] = point.y;

            let url = this._url + L.Util.getParamString(params, this._url, true);

            if (url) {
                $.ajax({
                    type: "GET",
                    url: url,
                    info_format: 'application/json',
                    success: function (data) {
                        if (data.features.length !== 0) {
                            $("#chart_modal").modal('show');
                            getstreamflow(data.features[0].properties['COMID'])
                        } else {
                            console.log('No features where you clicked so you got an error ' + data);
                        }
                    },
                });
            } else {
                console.log('Unable to extract the right GetFeatureInfo Url');
            }
        }
    },
});

L.tileLayer.WMFS = function (url, options) {
    return new L.TileLayer.WMFS(url, options);
};